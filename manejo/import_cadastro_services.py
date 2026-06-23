"""
Cadastro em lote de Propriedades e Espécies de Manejo Florestal.

Este é um modelo de planilha SEPARADO do de Entradas/Saídas (import_services.py).
Aqui só se cadastram Propriedades e Espécies — nenhum volume, data ou
movimento. A ideia é resolver o caso de participantes com muitas
propriedades/espécies novas: cadastra tudo de uma vez aqui, depois usa
os nomes exatos cadastrados na planilha de Entradas/Saídas.

Diferente do import_services.py (que NUNCA cria Propriedade/Espécie e
exige que já existam), este módulo EXISTE justamente para criá-las.
Se a propriedade ou espécie já existir, a linha é pulada com aviso
(não é tratada como erro — permite reenviar a mesma planilha sem medo
de duplicar).
"""
from decimal import Decimal

from reports.services import (
    safe_str,
    decimal_value,
    normalize_header,
    first_present,
    make_import_error,
)

from .models import Especie, Propriedade


def _cadastro_sheet_rows(sheet):
    """Parser de linhas para as abas Propriedades/Especies do Cadastro em Lote.

    Diferente de reports.services.sheet_rows (que procura a coluna 'data'
    para achar o header — adequado para Entradas/Saídas, mas inexistente
    aqui), este parser assume que o header está na primeira linha não vazia
    da planilha (varre até 5 linhas, por segurança)."""
    headers = []
    header_row_number = 1
    for row_number, row in enumerate(sheet.iter_rows(min_row=1, max_row=5, values_only=True), start=1):
        normalized = [normalize_header(cell) for cell in row]
        if any(normalized):
            headers = normalized
            header_row_number = row_number
            break

    data_start = header_row_number + 1
    for idx, row in enumerate(sheet.iter_rows(min_row=data_start, values_only=True), start=data_start):
        values = list(row)
        if not any(value not in (None, '') for value in values):
            continue
        payload = {}
        for pos, header in enumerate(headers):
            if header:
                payload[header] = values[pos] if pos < len(values) else None
        yield idx, payload


def count_cadastro_workbook_rows(workbook):
    total = 0
    for sheet_name in ('Propriedades', 'Especies'):
        if sheet_name in workbook.sheetnames:
            total += sum(1 for _idx, _row in _cadastro_sheet_rows(workbook[sheet_name]))
    return total


def build_cadastro_import_preview(workbook, participant, user, persist=False):
    """
    Processa a planilha de Cadastro em Lote (Propriedades + Espécies).
    Não há fases dependentes uma da outra (diferente de Entradas/Saídas) —
    as duas abas são independentes entre si.
    """
    summary = {'propriedades': 0, 'especies': 0, 'propriedades_existentes': 0, 'especies_existentes': 0}
    errors = []
    previews = {'propriedades': [], 'especies': []}

    if 'Propriedades' in workbook.sheetnames:
        sheet = workbook['Propriedades']
        for idx, row in _cadastro_sheet_rows(sheet):
            try:
                nome = safe_str(first_present(row, 'nome', 'propriedade'))
                if not nome:
                    raise ValueError('Nome da propriedade não informado.')

                codigo = safe_str(first_present(row, 'codigo', 'codigo_car', 'car'))
                municipio = safe_str(first_present(row, 'municipio'))
                uf = safe_str(first_present(row, 'uf'))[:2].upper()
                area_raw = first_present(row, 'area_hectares', 'area')
                area_hectares = decimal_value(area_raw) if area_raw not in (None, '') else None

                ja_existe = Propriedade.objects.filter(participant=participant, nome__iexact=nome).exists()

                preview = {
                    'linha': idx,
                    'nome': nome,
                    'codigo': codigo,
                    'municipio': municipio,
                    'uf': uf,
                    'area_hectares': area_hectares,
                    'ja_existia': ja_existe,
                }
                previews['propriedades'].append(preview)

                if ja_existe:
                    summary['propriedades_existentes'] += 1
                else:
                    summary['propriedades'] += 1
                    if persist:
                        Propriedade.objects.create(
                            participant=participant,
                            nome=nome,
                            codigo=codigo,
                            municipio=municipio,
                            uf=uf,
                            area_hectares=area_hectares,
                            ativa=True,
                        )
            except Exception as exc:
                errors.append(make_import_error('Propriedades', idx, exc, row))

    if 'Especies' in workbook.sheetnames:
        sheet = workbook['Especies']
        for idx, row in _cadastro_sheet_rows(sheet):
            try:
                nome = safe_str(first_present(row, 'nome', 'especie', 'espécie'))
                if not nome:
                    raise ValueError('Nome da espécie não informado.')

                fator_ton_raw = first_present(row, 'fator_ton', 'fator_m3_para_ton')
                fator_st_raw = first_present(row, 'fator_st', 'fator_m3_para_st')
                if fator_ton_raw in (None, ''):
                    raise ValueError('fator_ton não informado (obrigatório — usado na conversão de unidades).')
                if fator_st_raw in (None, ''):
                    raise ValueError('fator_st não informado (obrigatório — usado na conversão de unidades).')
                fator_ton = decimal_value(fator_ton_raw)
                fator_st = decimal_value(fator_st_raw)
                if fator_ton <= 0 or fator_st <= 0:
                    raise ValueError('fator_ton e fator_st devem ser maiores que zero.')

                ja_existe = Especie.objects.filter(participant=participant, nome__iexact=nome).exists()

                preview = {
                    'linha': idx,
                    'nome': nome,
                    'fator_ton': fator_ton,
                    'fator_st': fator_st,
                    'ja_existia': ja_existe,
                }
                previews['especies'].append(preview)

                if ja_existe:
                    summary['especies_existentes'] += 1
                else:
                    summary['especies'] += 1
                    if persist:
                        Especie.objects.create(
                            participant=participant,
                            nome=nome,
                            fator_m3_para_ton=fator_ton,
                            fator_m3_para_st=fator_st,
                            ativo=True,
                        )
            except Exception as exc:
                errors.append(make_import_error('Especies', idx, exc, row))

    return summary, errors, previews
