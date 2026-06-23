"""
Importação em lote de Manejo Florestal (Entradas de inventário e Saídas).

Reaproveita as funções genéricas de reports.services (parsing de planilha,
formatação de erros) e implementa a lógica de negócio própria do Manejo:
- Entrada identificada por Propriedade + Espécie (não por "documento" como no COC)
- Saída debita da entrada correspondente a essa mesma combinação
- Se houver mais de uma entrada para a mesma Propriedade+Espécie, é erro
  (no Manejo deve existir apenas UM inventário consolidado por combinação)
- Propriedade e Espécie NÃO são criadas automaticamente aqui — devem já
  existir no cadastro do participante. Para cadastrar várias de uma vez,
  use o modelo de Cadastro em Lote (manejo/import_cadastro_services.py),
  que cria apenas Propriedades e Espécies, sem nenhum dado de movimento.
"""
from decimal import Decimal

from reports.services import (
    safe_str,
    normalize_date,
    decimal_value,
    sheet_rows,
    first_present,
    make_import_error,
)

from .models import Especie, Propriedade, InventarioEntrada, SaidaManejo


UNIDADES_VALIDAS = {'m3', 'ton', 'st'}


def count_manejo_workbook_rows(workbook):
    total = 0
    for sheet_name in ('Entradas', 'Saidas'):
        if sheet_name in workbook.sheetnames:
            total += sum(1 for _idx, _row in sheet_rows(workbook[sheet_name]))
    return total


def _get_propriedade(participant, nome):
    nome = safe_str(nome)
    if not nome:
        raise ValueError('Propriedade não informada.')
    propriedade = Propriedade.objects.filter(participant=participant, nome__iexact=nome).first()
    if propriedade is None:
        raise ValueError(
            f'Propriedade "{nome}" não encontrada para este participante. '
            f'Cadastre a propriedade antes de importar (manualmente ou via modelo de Cadastro em Lote).'
        )
    return propriedade


def _get_especie(participant, nome):
    nome = safe_str(nome)
    if not nome:
        raise ValueError('Espécie não informada.')
    especie = Especie.objects.filter(participant=participant, nome__iexact=nome).first()
    if especie is None:
        raise ValueError(
            f'Espécie "{nome}" não encontrada para este participante. '
            f'Cadastre a espécie antes de importar (manualmente ou via modelo de Cadastro em Lote).'
        )
    return especie


def _validar_unidade(unidade):
    unidade = safe_str(unidade).lower() or 'm3'
    if unidade not in UNIDADES_VALIDAS:
        raise ValueError(f'Unidade "{unidade}" inválida. Use m3, ton ou st.')
    return unidade


def _find_entrada_unica(participant, propriedade, especie):
    """Localiza a ÚNICA entrada de inventário para esta Propriedade+Espécie.
    Se houver mais de uma, é um erro de cadastro que precisa ser corrigido
    manualmente — o Manejo assume inventário consolidado (1 entrada por
    combinação), então múltiplas entradas indicam duplicidade indesejada."""
    entradas = list(InventarioEntrada.objects.filter(participant=participant, propriedade=propriedade, especie=especie))
    if not entradas:
        raise ValueError(
            f'Nenhuma entrada de inventário encontrada para "{propriedade.nome}" + "{especie.nome}". '
            f'Cadastre a entrada antes de lançar saídas para esta combinação.'
        )
    if len(entradas) > 1:
        raise ValueError(
            f'Existem {len(entradas)} entradas de inventário para "{propriedade.nome}" + "{especie.nome}". '
            f'O Manejo espera um único inventário consolidado por propriedade+espécie — '
            f'consolide ou remova os registros duplicados antes de importar saídas.'
        )
    return entradas[0]


def build_manejo_import_preview(workbook, participant, user, persist=False):
    """
    Processa a planilha de Manejo em duas fases quando persist=True:
      Fase 1 — Entradas: grava todos os inventários.
      Fase 2 — Saídas: agora encontram as entradas da fase 1 (ou já existentes).
    No modo preview (persist=False) tudo roda sem gravar, apenas validando.
    """
    summary = {'entradas': 0, 'saidas': 0}
    errors = []
    previews = {'entradas': [], 'saidas': []}

    if 'Entradas' in workbook.sheetnames:
        sheet = workbook['Entradas']
        for idx, row in sheet_rows(sheet):
            try:
                data = first_present(row, 'data')
                if not data:
                    raise ValueError('Data não informada.')
                propriedade_nome = first_present(row, 'propriedade')
                especie_nome = first_present(row, 'especie', 'espécie')
                documento = first_present(row, 'documento')
                volume = first_present(row, 'volume', 'quantidade')
                unidade = first_present(row, 'unidade')
                observacoes = first_present(row, 'observacoes')

                propriedade = _get_propriedade(participant, propriedade_nome)
                especie = _get_especie(participant, especie_nome)
                unidade = _validar_unidade(unidade)
                volume = decimal_value(volume)
                if volume <= 0:
                    raise ValueError('Volume deve ser maior que zero.')
                volume_m3 = especie.converter_para_m3(volume, unidade)

                # Mesma regra de consolidação: se já existir entrada para esta
                # combinação, a importação deste tipo de planilha não deve
                # criar uma segunda — bloqueia para evitar duplicidade.
                ja_existe = InventarioEntrada.objects.filter(
                    participant=participant, propriedade=propriedade, especie=especie
                ).exists()
                if ja_existe:
                    raise ValueError(
                        f'Já existe uma entrada de inventário para "{propriedade.nome}" + "{especie.nome}". '
                        f'Edite a entrada existente em vez de importar uma nova (o Manejo não permite duplicar '
                        f'inventário da mesma propriedade+espécie).'
                    )

                preview = {
                    'linha': idx,
                    'data': data,
                    'propriedade': propriedade.nome,
                    'especie': especie.nome,
                    'documento': safe_str(documento),
                    'volume': volume,
                    'unidade': unidade,
                    'volume_m3': volume_m3,
                }
                previews['entradas'].append(preview)
                summary['entradas'] += 1

                if persist:
                    InventarioEntrada.objects.create(
                        participant=participant,
                        propriedade=propriedade,
                        especie=especie,
                        data=normalize_date(data),
                        documento=safe_str(documento),
                        volume=volume,
                        unidade=unidade,
                        volume_m3=volume_m3,
                        observacoes=safe_str(observacoes),
                        created_by=user,
                    )
            except Exception as exc:
                errors.append(make_import_error('Entradas', idx, exc, row))

    if 'Saidas' in workbook.sheetnames:
        sheet = workbook['Saidas']
        for idx, row in sheet_rows(sheet):
            try:
                data = first_present(row, 'data')
                if not data:
                    raise ValueError('Data não informada.')
                propriedade_nome = first_present(row, 'propriedade')
                especie_nome = first_present(row, 'especie', 'espécie')
                documento = first_present(row, 'documento')
                cliente_nome = first_present(row, 'cliente')
                declaracao = first_present(row, 'declaracao_fsc')
                volume = first_present(row, 'volume', 'quantidade')
                unidade = first_present(row, 'unidade')
                observacoes = first_present(row, 'observacoes')

                propriedade = _get_propriedade(participant, propriedade_nome)
                especie = _get_especie(participant, especie_nome)
                unidade = _validar_unidade(unidade)
                volume = decimal_value(volume)
                if volume <= 0:
                    raise ValueError('Volume deve ser maior que zero.')
                volume_m3 = especie.converter_para_m3(volume, unidade)

                entrada = _find_entrada_unica(participant, propriedade, especie)

                # Valida saldo disponível (mesma regra usada no form manual)
                saldo = entrada.saldo_disponivel_m3
                if volume_m3 > saldo:
                    raise ValueError(
                        f'Saldo insuficiente em "{propriedade.nome}" + "{especie.nome}". '
                        f'Disponível: {saldo:.4f} m³. Solicitado: {volume_m3:.4f} m³.'
                    )

                declaracao_fsc = True
                declaracao_str = safe_str(declaracao).lower()
                if declaracao_str in ('não', 'nao', 'false', '0', 'n'):
                    declaracao_fsc = False

                preview = {
                    'linha': idx,
                    'data': data,
                    'propriedade': propriedade.nome,
                    'especie': especie.nome,
                    'documento': safe_str(documento),
                    'cliente': safe_str(cliente_nome),
                    'volume': volume,
                    'unidade': unidade,
                    'volume_m3': volume_m3,
                }
                previews['saidas'].append(preview)
                summary['saidas'] += 1

                if persist:
                    SaidaManejo.objects.create(
                        participant=participant,
                        entrada=entrada,
                        data=normalize_date(data),
                        documento=safe_str(documento),
                        cliente_nome=safe_str(cliente_nome),
                        declaracao_fsc=declaracao_fsc,
                        volume=volume,
                        unidade=unidade,
                        volume_m3=volume_m3,
                        observacoes=safe_str(observacoes),
                        created_by=user,
                    )
                    # Recarrega para refletir o débito em validações subsequentes
                    # na mesma linha de propriedade+espécie, dentro da mesma planilha.
                    entrada.refresh_from_db()
            except Exception as exc:
                errors.append(make_import_error('Saidas', idx, exc, row))

    return summary, errors, previews
