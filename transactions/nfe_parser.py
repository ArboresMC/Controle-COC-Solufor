"""
Parser de XML da NF-e (versao 4.0) para pre-preenchimento do formulario de Entrada.
Extrai: numero do documento, data de emissao, emitente (fornecedor), produto,
quantidade e unidade comercial. Nao depende de nenhuma API externa.
"""
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

# Namespace padrao da NF-e v4.0
_NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

# Mapeamento de unidades comerciais da NF-e para as unidades do TraceFlor
UNIT_MAP = {
    # Tonelada
    'T': 't', 'TON': 't', 'TN': 't', 'TONELADA': 't', 'TONELADAS': 't',
    'TON.': 't', 'T.': 't',
    # Metro cubico
    'M3': 'm3', 'M³': 'm3', 'MTR³': 'm3', 'M.C.': 'm3', 'MC': 'm3',
    'M3.': 'm3', 'MT3': 'm3', 'METRO CUBICO': 'm3', 'METROS CUBICOS': 'm3',
    # Metro estereo / mst
    'ST': 'mst', 'MST': 'mst', 'M.ST': 'mst', 'M.ST.': 'mst',
    'ESTERE': 'mst', 'ESTEREO': 'mst', 'ESTÉREO': 'mst',
}


def _find(element, tag, ns=_NS):
    """Helper: find com namespace ou sem (para XMLs que omitem namespace)."""
    result = element.find(f'nfe:{tag}', ns)
    if result is None:
        result = element.find(tag)
    return result


def _text(element, tag, default=''):
    """Retorna o texto de uma tag filha, ou default se nao existir."""
    el = _find(element, tag)
    return (el.text or '').strip() if el is not None else default


def parse_nfe_xml(xml_bytes):
    """
    Recebe o conteudo do arquivo XML da NF-e como bytes.
    Retorna um dict com os campos extraidos, ou levanta ValueError com
    uma mensagem clara se o arquivo nao for uma NF-e valida.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f'Arquivo XML invalido: {exc}') from exc

    # Tenta localizar a tag <infNFe> com ou sem namespace
    inf = root.find('.//nfe:infNFe', _NS) or root.find('.//infNFe')
    if inf is None:
        raise ValueError('Arquivo nao reconhecido como NF-e. Tag <infNFe> nao encontrada.')

    ide = _find(inf, 'ide')
    emit = _find(inf, 'emit')
    if ide is None or emit is None:
        raise ValueError('Estrutura da NF-e invalida: blocos <ide> ou <emit> ausentes.')

    # --- Dados da nota ---
    numero = _text(ide, 'nNF')
    serie = _text(ide, 'serie')
    dh_emi = _text(ide, 'dhEmi') or _text(ide, 'dEmi')  # dhEmi (v4) ou dEmi (v2/3)
    data_emissao = dh_emi[:10] if dh_emi else ''  # "2026-06-12T10:30:00-03:00" -> "2026-06-12"

    # Converte "2026-06-12" para "12/06/2026" (formato esperado pelo DateInput do Django)
    if data_emissao and '-' in data_emissao:
        partes = data_emissao.split('-')
        if len(partes) == 3:
            data_emissao = f'{partes[2]}/{partes[1]}/{partes[0]}'

    doc_number = f'{numero}/{serie}' if serie and serie != '0' else numero

    # --- Emitente (fornecedor) ---
    cnpj_emit = _text(emit, 'CNPJ')
    nome_emit = _text(emit, 'xNome')

    # --- Itens (det) ---
    itens = []
    for det in (inf.findall('nfe:det', _NS) or inf.findall('det')):
        prod = _find(det, 'prod')
        if prod is None:
            continue
        x_prod = _text(prod, 'xProd')
        q_com_raw = _text(prod, 'qCom')
        u_com_raw = _text(prod, 'uCom').upper().strip()

        try:
            quantidade = Decimal(q_com_raw.replace(',', '.'))
        except InvalidOperation:
            quantidade = None

        unidade_nfe = u_com_raw
        unidade_traceflor = UNIT_MAP.get(u_com_raw)

        itens.append({
            'descricao': x_prod,
            'quantidade': str(quantidade) if quantidade is not None else '',
            'unidade_nfe': unidade_nfe,
            'unidade_traceflor': unidade_traceflor or '',
            'unidade_mapeada': unidade_traceflor is not None,
        })

    if not itens:
        raise ValueError('Nenhum item de produto encontrado na NF-e.')

    return {
        'document_number': doc_number,
        'movement_date': data_emissao,
        'supplier_cnpj': cnpj_emit,
        'supplier_name': nome_emit,
        'itens': itens,
        # Atalho para NF-e com item unico (caso mais comum na operacao florestal)
        'item_unico': itens[0] if len(itens) == 1 else None,
    }
