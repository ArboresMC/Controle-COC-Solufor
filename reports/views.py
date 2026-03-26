from decimal import Decimal
from unicodedata import normalize

from django.db import transaction
from io import BytesIO

import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from catalog.models import Counterparty, Product
from participants.models import Participant
from transactions.models import EntryRecord, LotAllocation, SaleRecord, TraceLot, TransformationRecord
from transactions.services import (
    build_traceability_rows,
    calculate_target_from_source,
    convert_to_base,
    get_entry_balance_rows,
    get_lot_remaining_for_sale,
    get_lot_remaining_for_transformation,
    get_transformation_rule,
    reallocate_sale,
    reallocate_transformation_sources,
    sync_entry_lot,
    sync_transformation_metadata,
    sync_transformation_target_lot,
)
from .forms import ImportWorkbookForm


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager


def _safe_str(value):
    return '' if value is None else str(value).strip()


def _normalize_date(value):
    if hasattr(value, 'date'):
        return value.date()
    return value


def _decimal(value):
    return Decimal(str(value)) if value not in (None, '') else Decimal('0')


def _normalize_header(value):
    text = normalize('NFKD', _safe_str(value)).encode('ascii', 'ignore').decode('ascii')
    return text.lower().replace(' ', '_')




def _parse_multi_value(value):
    text = _safe_str(value)
    if not text:
        return []
    return [item.strip() for item in text.split(';') if item is not None and str(item).strip()]


def _get_lot_by_identifier(participant, product, *, lot_id=None, document_number=None, batch_code=None, allowed_source_types=None):
    qs = TraceLot.objects.select_related('entry', 'transformation', 'product', 'supplier').filter(participant=participant, product=product)
    if allowed_source_types:
        qs = qs.filter(source_type__in=allowed_source_types)
    if lot_id not in (None, ''):
        try:
            return qs.get(pk=int(str(lot_id).strip()))
        except Exception:
            raise ValueError(f'Lote de origem com ID {lot_id} não foi encontrado para o produto informado.')

    document_number = _safe_str(document_number)
    batch_code = _safe_str(batch_code)
    if not document_number and not batch_code:
        raise ValueError('Informe id_lote_origem ou documento_origem/lote_origem.')

    matches = []
    for lot in qs:
        lot_doc = ''
        lot_batch = ''
        if lot.entry_id:
            lot_doc = _safe_str(lot.entry.document_number)
            lot_batch = _safe_str(lot.entry.batch_code)
        elif lot.transformation_id:
            lot_doc = _safe_str(lot.transformation.document_number)
        if document_number and lot_doc != document_number:
            continue
        if batch_code and lot_batch != batch_code:
            continue
        matches.append(lot)

    if not matches:
        raise ValueError('Não foi encontrado lote compatível com a origem informada.')
    if len(matches) > 1:
        raise ValueError('Origem ambígua. Use id_lote_origem para identificar o lote exatamente.')
    return matches[0]


def _build_manual_lot_specs(row, *, require_quantities=False):
    lot_ids = _parse_multi_value(_first_present(row, 'id_lote_origem'))
    source_types = _parse_multi_value(_first_present(row, 'origem_tipo'))
    documents = _parse_multi_value(_first_present(row, 'documento_origem'))
    batches = _parse_multi_value(_first_present(row, 'lote_origem'))
    quantities = _parse_multi_value(_first_present(row, 'quantidade_origem'))

    item_count = max(len(lot_ids), len(source_types), len(documents), len(batches), len(quantities))
    if item_count == 0:
        return []

    if require_quantities and len(quantities) != item_count:
        raise ValueError('Quando informar origem manual, preencha quantidade_origem para todas as origens.')

    specs = []
    for index in range(item_count):
        specs.append({
            'lot_id': lot_ids[index] if index < len(lot_ids) else '',
            'source_type': (source_types[index] if index < len(source_types) else '').lower(),
            'document_number': documents[index] if index < len(documents) else '',
            'batch_code': batches[index] if index < len(batches) else '',
            'quantity_base': _decimal(quantities[index]) if index < len(quantities) else Decimal('0'),
        })

    return specs


def _resolve_manual_lots(participant, product, specs, *, sale=None, transformation=None, allowed_source_types=None):
    resolved = []
    total = Decimal('0')
    for spec in specs:
        lot = _get_lot_by_identifier(
            participant,
            product,
            lot_id=spec.get('lot_id'),
            document_number=spec.get('document_number'),
            batch_code=spec.get('batch_code'),
            allowed_source_types=allowed_source_types,
        )
        declared_source_type = _safe_str(spec.get('source_type')).lower()
        if declared_source_type and declared_source_type != lot.source_type:
            raise ValueError(f'O lote {lot.id} é do tipo {lot.source_type}, diferente do origem_tipo informado.')
        quantity_base = _decimal(spec.get('quantity_base'))
        remaining = get_lot_remaining_for_sale(lot, sale=sale) if sale is not None else get_lot_remaining_for_transformation(lot, transformation=transformation)
        if quantity_base <= 0:
            raise ValueError(f'Informe quantidade_origem maior que zero para o lote {lot.id}.')
        if remaining < quantity_base:
            raise ValueError(f'Lote {lot.id} sem saldo suficiente. Disponível: {remaining}. Solicitado: {quantity_base}.')
        resolved.append((lot, quantity_base))
        total += quantity_base
    return resolved, total.quantize(Decimal('0.001'))


def _apply_manual_sale_allocations(sale, resolved_allocations):
    sale.lot_allocations.all().delete()
    selected_supplier = None
    selected_claim = ''
    for lot, quantity_base in resolved_allocations:
        lot_claim = (lot.fsc_claim or '').strip()
        if selected_supplier is None:
            selected_supplier = lot.supplier
        elif lot.supplier_id != getattr(selected_supplier, 'id', None):
            raise ValueError('A saída não pode consumir lotes de fornecedores diferentes.')
        if selected_claim and lot_claim != selected_claim:
            raise ValueError('A saída não pode consumir lotes com declarações FSC diferentes.')
        if not selected_claim:
            selected_claim = lot_claim
        LotAllocation.objects.create(
            participant=sale.participant,
            lot=lot,
            sale=sale,
            target_type='sale',
            quantity_base=quantity_base.quantize(Decimal('0.001')),
        )
    sale.supplier = selected_supplier
    sale.fsc_claim = selected_claim or sale.fsc_claim
    sale.save(update_fields=['supplier', 'fsc_claim'])


def _apply_manual_transformation_allocations(transformation, resolved_allocations):
    transformation.source_lot_allocations.all().delete()
    for lot, quantity_base in resolved_allocations:
        LotAllocation.objects.create(
            participant=transformation.participant,
            lot=lot,
            transformation=transformation,
            target_type='transformation',
            quantity_base=quantity_base.quantize(Decimal('0.001')),
        )
    sync_transformation_metadata(transformation)
    sync_transformation_target_lot(transformation)


def _get_available_import_lots(participant):
    if not participant:
        return []
    lots = (
        TraceLot.objects
        .select_related('product', 'supplier', 'entry', 'transformation', 'transformation__source_product')
        .filter(participant=participant)
        .order_by('movement_date', 'id')
    )
    items = []
    for lot in lots:
        remaining = get_lot_remaining_for_transformation(lot) if lot.source_type == 'entry' else get_lot_remaining_for_sale(lot)
        if remaining <= 0:
            continue
        document_number = _safe_str(lot.entry.document_number if lot.entry_id else lot.transformation.document_number if lot.transformation_id else '')
        batch_code = _safe_str(lot.entry.batch_code) if lot.entry_id else ''
        usage_hint = 'saida/transformacao' if lot.source_type == 'entry' else 'saida'
        items.append({
            'id': lot.id,
            'source_type': lot.source_type,
            'usage_hint': usage_hint,
            'document_number': document_number,
            'batch_code': batch_code,
            'product': lot.product.name,
            'remaining': remaining.quantize(Decimal('0.001')),
            'unit': lot.product.get_unit_display(),
            'supplier': str(lot.supplier) if lot.supplier_id else '',
            'movement_date': lot.movement_date,
            'fsc_claim': _safe_str(lot.fsc_claim),
            'label': lot.label,
        })
    return items

def _sheet_rows(sheet):
    headers = [_normalize_header(cell) for cell in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), [])]
    for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        values = list(row)
        if not any(value not in (None, '') for value in values):
            continue
        payload = {}
        for pos, header in enumerate(headers):
            if header:
                payload[header] = values[pos] if pos < len(values) else None
        yield idx, payload


def _first_present(row, *keys):
    for key in keys:
        if key in row:
            return row.get(key)
    return None


def _coerce_product(product_name, *, default_unit=None, create_if_missing=False):
    product_name = _safe_str(product_name)
    if not product_name:
        raise ValueError('Produto não informado.')
    if create_if_missing:
        product, _ = Product.objects.get_or_create(
            name=product_name,
            defaults={'unit': default_unit or 'm3', 'active': True},
        )
        return product
    return Product.objects.get(name=product_name)


def _get_or_create_counterparty(participant, name, *, type_):
    normalized_name = _safe_str(name)
    if not normalized_name:
        return None
    return Counterparty.objects.get_or_create(
        participant=participant,
        name=normalized_name,
        defaults={'type': type_},
    )[0]


def _build_import_preview(workbook, participant, user, persist=False):
    summary = {'entries': 0, 'sales': 0, 'transformations': 0}
    errors = []
    previews = {'entries': [], 'sales': [], 'transformations': []}

    if 'Entradas' in workbook.sheetnames:
        sheet = workbook['Entradas']
        for idx, row in _sheet_rows(sheet):
            try:
                data = _first_present(row, 'data')
                if not data:
                    raise ValueError('Data não informada.')
                documento = _first_present(row, 'documento')
                fornecedor_nome = _first_present(row, 'fornecedor')
                produto_nome = _first_present(row, 'produto')
                quantidade = _first_present(row, 'quantidade')
                unidade = _first_present(row, 'unidade')
                declaracao = _first_present(row, 'declaracao_fsc')
                lote = _first_present(row, 'lote')
                observacoes = _first_present(row, 'observacoes')

                unidade = _safe_str(unidade) or 'm3'
                product = _coerce_product(produto_nome, default_unit=unidade, create_if_missing=True)
                supplier_name = _safe_str(fornecedor_nome) or 'Não informado'
                supplier = _get_or_create_counterparty(participant, supplier_name, type_='supplier')
                quantidade = _decimal(quantidade)
                quantity_base = convert_to_base(product, quantidade, unidade)
                preview = {
                    'linha': idx,
                    'data': data,
                    'documento': _safe_str(documento),
                    'supplier': supplier_name,
                    'product': product.name,
                    'quantity': quantidade,
                    'unit': unidade,
                    'quantity_base': quantity_base,
                }
                previews['entries'].append(preview)
                summary['entries'] += 1
                if persist:
                    obj = EntryRecord.objects.create(
                        participant=participant,
                        movement_date=_normalize_date(data),
                        document_number=_safe_str(documento),
                        supplier=supplier,
                        product=product,
                        quantity=quantidade,
                        movement_unit=unidade,
                        unit_snapshot=product.unit,
                        quantity_base=quantity_base,
                        fsc_claim=_safe_str(declaracao),
                        batch_code=_safe_str(lote),
                        notes=_safe_str(observacoes),
                        created_by=user,
                        status='submitted',
                    )
                    sync_entry_lot(obj)
            except Exception as exc:
                errors.append(f'Entradas linha {idx}: {exc}')

    if 'Saidas' in workbook.sheetnames:
        sheet = workbook['Saidas']
        for idx, row in _sheet_rows(sheet):
            try:
                data = _first_present(row, 'data')
                if not data:
                    raise ValueError('Data não informada.')
                documento = _first_present(row, 'documento')
                cliente_nome = _first_present(row, 'cliente')
                produto_nome = _first_present(row, 'produto')
                quantidade = _first_present(row, 'quantidade')
                unidade = _first_present(row, 'unidade')
                declaracao = _first_present(row, 'declaracao_fsc')
                lote = _first_present(row, 'lote')
                observacoes = _first_present(row, 'observacoes')

                product = _coerce_product(produto_nome)
                customer_name = _safe_str(cliente_nome)
                if not customer_name:
                    raise ValueError('Cliente não informado.')
                customer = _get_or_create_counterparty(participant, customer_name, type_='customer')
                quantidade = _decimal(quantidade)
                unidade = _safe_str(unidade) or product.unit
                quantity_base = convert_to_base(product, quantidade, unidade)
                manual_specs = _build_manual_lot_specs(row, require_quantities=False)
                manual_lots = []
                if manual_specs:
                    manual_lots, manual_total = _resolve_manual_lots(
                        participant,
                        product,
                        manual_specs,
                        sale=None,
                        allowed_source_types=['entry', 'transformation'],
                    )
                    if manual_total != quantity_base:
                        raise ValueError(f'A soma de quantidade_origem ({manual_total}) difere da quantidade da saída ({quantity_base}).')

                preview = {
                    'linha': idx,
                    'data': data,
                    'documento': _safe_str(documento),
                    'customer': customer_name,
                    'product': product.name,
                    'quantity': quantidade,
                    'unit': unidade,
                    'quantity_base': quantity_base,
                    'manual_lots': [f"#{lot.id} {lot.label} ({qty})" for lot, qty in manual_lots],
                }
                previews['sales'].append(preview)
                summary['sales'] += 1
                if persist:
                    obj = SaleRecord.objects.create(
                        participant=participant,
                        movement_date=_normalize_date(data),
                        document_number=_safe_str(documento),
                        customer=customer,
                        product=product,
                        quantity=quantidade,
                        movement_unit=unidade,
                        unit_snapshot=product.unit,
                        quantity_base=quantity_base,
                        fsc_claim=_safe_str(declaracao),
                        batch_code=_safe_str(lote),
                        notes=_safe_str(observacoes),
                        created_by=user,
                        status='submitted',
                    )
                    if manual_lots:
                        _apply_manual_sale_allocations(obj, manual_lots)
                    else:
                        reallocate_sale(obj)
            except Exception as exc:
                errors.append(f'Saidas linha {idx}: {exc}')

    if 'Transformacoes' in workbook.sheetnames:
        sheet = workbook['Transformacoes']
        for idx, row in _sheet_rows(sheet):
            try:
                data = _first_present(row, 'data')
                if not data:
                    raise ValueError('Data não informada.')
                documento = _first_present(row, 'documento')
                cliente_nome = _first_present(row, 'cliente', 'cliente_final')
                produto_origem = _first_present(row, 'produto_origem')
                produto_destino = _first_present(row, 'produto_destino')
                target_quantity = _first_present(row, 'quantidade_produzida', 'quantidade_destino', 'quantidade_producao')
                target_unit = _first_present(row, 'unidade_destino', 'unidade_produzida', 'unidade')
                observacoes = _first_present(row, 'observacoes')

                source_product = _coerce_product(produto_origem)
                target_product = _coerce_product(produto_destino)
                if source_product.id == target_product.id:
                    raise ValueError('Produto de origem e produto de destino não podem ser iguais.')

                rule = get_transformation_rule(source_product, target_product, participant=participant)
                if not rule:
                    raise ValueError('Não existe regra de transformação cadastrada para os produtos selecionados para esta empresa.')

                target_quantity = _decimal(target_quantity)
                target_unit = _safe_str(target_unit) or target_product.unit
                target_quantity_base = convert_to_base(target_product, target_quantity, target_unit)
                if not rule.yield_factor:
                    raise ValueError('A regra de transformação está com fator de rendimento inválido.')
                source_quantity_base = (target_quantity_base / Decimal(str(rule.yield_factor))).quantize(Decimal('0.001'))

                manual_specs = _build_manual_lot_specs(row, require_quantities=False)
                manual_lots = []
                if manual_specs:
                    manual_lots, manual_total = _resolve_manual_lots(
                        participant,
                        source_product,
                        manual_specs,
                        transformation=None,
                        allowed_source_types=['entry'],
                    )
                    if manual_total != source_quantity_base:
                        raise ValueError(f'A soma de quantidade_origem ({manual_total}) difere do consumo calculado da origem ({source_quantity_base}).')

                preview = {
                    'linha': idx,
                    'data': data,
                    'document_number': _safe_str(documento),
                    'customer': _safe_str(cliente_nome),
                    'source_product': source_product.name,
                    'source_quantity_base': source_quantity_base,
                    'source_unit': source_product.unit,
                    'target_product': target_product.name,
                    'target_quantity': target_quantity,
                    'target_unit': target_unit,
                    'target_quantity_base': target_quantity_base,
                    'yield_factor': rule.yield_factor,
                    'manual_lots': [f"#{lot.id} {lot.label} ({qty})" for lot, qty in manual_lots],
                }
                previews['transformations'].append(preview)
                summary['transformations'] += 1
                if persist:
                    customer = _get_or_create_counterparty(participant, cliente_nome, type_='customer') if _safe_str(cliente_nome) else None
                    obj = TransformationRecord.objects.create(
                        participant=participant,
                        movement_date=_normalize_date(data),
                        document_number=_safe_str(documento),
                        customer=customer,
                        source_product=source_product,
                        source_quantity=source_quantity_base,
                        source_unit=source_product.unit,
                        source_quantity_base=source_quantity_base,
                        target_product=target_product,
                        target_quantity_base=target_quantity_base,
                        target_unit_snapshot=target_product.unit,
                        yield_factor_snapshot=rule.yield_factor,
                        notes=_safe_str(observacoes),
                        created_by=user,
                    )
                    if manual_lots:
                        _apply_manual_transformation_allocations(obj, manual_lots)
                    else:
                        reallocate_transformation_sources(obj)
                        sync_transformation_target_lot(obj)
            except Exception as exc:
                errors.append(f'Transformacoes linha {idx}: {exc}')

    return summary, errors, previews


class ConsolidatedExcelReportView(ManagerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = 'Entradas'
        ws1.append(['Data', 'Participante', 'Documento', 'Fornecedor', 'Produto', 'Qtd informada', 'Unidade informada', 'Qtd base', 'Unidade base', 'Declaração FSC', 'Status'])
        for obj in EntryRecord.objects.select_related('participant', 'supplier', 'product'):
            ws1.append([obj.movement_date.strftime('%d/%m/%Y'), str(obj.participant), obj.document_number, str(obj.supplier), str(obj.product), float(obj.quantity), obj.movement_unit, float(obj.quantity_base), obj.unit_snapshot, obj.fsc_claim, obj.get_status_display()])

        ws2 = wb.create_sheet('Saídas')
        ws2.append(['Data', 'Participante', 'Documento', 'Cliente', 'Produto', 'Qtd informada', 'Unidade informada', 'Qtd base', 'Unidade base', 'Declaração FSC', 'Status'])
        for obj in SaleRecord.objects.select_related('participant', 'customer', 'product'):
            ws2.append([obj.movement_date.strftime('%d/%m/%Y'), str(obj.participant), obj.document_number, str(obj.customer), str(obj.product), float(obj.quantity), obj.movement_unit, float(obj.quantity_base), obj.unit_snapshot, obj.fsc_claim, obj.get_status_display()])

        ws3 = wb.create_sheet('Transformações')
        ws3.append(['Data', 'Participante', 'Documento', 'Cliente final', 'Fornecedor origem', 'Declaração FSC', 'Produto origem', 'Qtd origem', 'Unidade origem', 'Qtd origem base', 'Produto destino', 'Qtd destino base', 'Unidade base destino', 'Fator'])
        for obj in TransformationRecord.objects.select_related('participant', 'source_product', 'target_product'):
            ws3.append([obj.movement_date.strftime('%d/%m/%Y'), str(obj.participant), obj.document_number, str(obj.customer) if obj.customer else '', str(obj.supplier) if obj.supplier else '', obj.fsc_claim, str(obj.source_product), float(obj.source_quantity), obj.source_unit, float(obj.source_quantity_base), str(obj.target_product), float(obj.target_quantity_base), obj.target_unit_snapshot, float(obj.yield_factor_snapshot)])

        ws4 = wb.create_sheet('Rastreabilidade')
        ws4.append(['Participante', 'Produto', 'Tipo de uso', 'Uso', 'Data uso', 'Fornecedor origem', 'Cliente / destino', 'Origem consumida', 'Data origem', 'Quantidade', 'Unidade'])
        for row in build_traceability_rows():
            ws4.append([str(row['participant']), str(row['product']), row['use_type'], row['use_label'], row['use_date'].strftime('%d/%m/%Y'), row['supplier'], row['counterparty'], row['source_label'], row['source_date'].strftime('%d/%m/%Y'), float(row['quantity']), row['unit']])

        ws5 = wb.create_sheet('Saldo por entrada')
        ws5.append(['Participante', 'Data entrada', 'Documento entrada', 'Fornecedor', 'Produto', 'Qtd entrada', 'Qtd vendida', 'Qtd transformada', 'Saldo remanescente', 'Unidade', 'Clientes atendidos'])
        for row in get_entry_balance_rows():
            ws5.append([str(row['participant']), row['movement_date'].strftime('%d/%m/%Y'), row['entry'].document_number, str(row['supplier']) if row['supplier'] else '', str(row['product']), float(row['quantity_total']), float(row['quantity_sold']), float(row['quantity_transformed']), float(row['quantity_remaining']), row['unit'], row['customers']])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f'relatorio_fsc_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        wb.save(response)
        return response


class AuditPdfReportView(ManagerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        participant_id = request.GET.get('participant')
        participant = Participant.objects.filter(pk=participant_id).first() if participant_id else None
        rows = build_traceability_rows(participant=participant)[:80]
        entry_balances = get_entry_balance_rows(participant=participant)[:80]

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=relatorio_auditoria_fsc_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        doc = SimpleDocTemplate(response, pagesize=landscape(A4), leftMargin=24, rightMargin=24, topMargin=24, bottomMargin=24)
        styles = getSampleStyleSheet()
        story = [
            Paragraph('Solufor Soluções Florestais', styles['Title']),
            Paragraph('Relatório de auditoria FSC — rastreabilidade e saldo por entrada', styles['Heading2']),
            Spacer(1, 12),
        ]
        if participant:
            story.append(Paragraph(f'Participante filtrado: {participant}', styles['Normal']))
            story.append(Spacer(1, 10))

        story.append(Paragraph('Rastreabilidade fornecedor → cliente', styles['Heading3']))
        trace_table = [['Participante', 'Produto', 'Uso', 'Fornecedor origem', 'Cliente / destino', 'Qtd']]
        for row in rows:
            trace_table.append([
                str(row['participant']), str(row['product']), row['use_label'], row['supplier'], row['counterparty'],
                f"{row['quantity']} {row['unit']}"
            ])
        table = Table(trace_table, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#14532d')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(table)
        story.append(Spacer(1, 14))

        story.append(Paragraph('Saldo por entrada / lote', styles['Heading3']))
        bal_table = [['Participante', 'Entrada', 'Fornecedor', 'Produto', 'Qtd entrada', 'Saldo remanescente']]
        for row in entry_balances:
            bal_table.append([
                str(row['participant']), row['entry'].document_number, str(row['supplier'] or ''), str(row['product']),
                f"{row['quantity_total']} {row['unit']}", f"{row['quantity_remaining']} {row['unit']}"
            ])
        table2 = Table(bal_table, repeatRows=1)
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1f2937')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.3, colors.grey),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(table2)
        doc.build(story)
        return response


class TraceabilityReportView(ManagerRequiredMixin, View):
    template_name = 'reports/traceability_report.html'

    def get(self, request, *args, **kwargs):
        participant_id = request.GET.get('participant')
        participant = Participant.objects.filter(pk=participant_id).first() if participant_id else None
        rows = build_traceability_rows(participant=participant)
        entry_balances = get_entry_balance_rows(participant=participant)
        return render(request, self.template_name, {
            'rows': rows,
            'entry_balances': entry_balances,
            'participants': Participant.objects.filter(status='active'),
            'selected_participant': participant,
        })


class ImportTemplateDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        participant = None
        participant_id = request.GET.get('participant')
        if request.user.is_manager:
            if participant_id:
                participant = Participant.objects.filter(pk=participant_id).first()
        else:
            participant = getattr(request.user, 'participant', None)

        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = 'Entradas'
        ws1.append(['data', 'documento', 'fornecedor', 'produto', 'quantidade', 'unidade', 'declaracao_fsc', 'lote', 'observacoes'])
        ws1.append(['2026-03-18', 'NF-ENT-001', 'Fornecedor Exemplo', 'Toras e Toretes 100%', 10, 't', 'FSC 100%', 'L001', 'Exemplo'])

        ws2 = wb.create_sheet('Saidas')
        ws2.append(['data', 'documento', 'cliente', 'produto', 'quantidade', 'unidade', 'declaracao_fsc', 'lote', 'id_lote_origem', 'origem_tipo', 'documento_origem', 'lote_origem', 'quantidade_origem', 'observacoes'])
        ws2.append(['2026-03-18', 'NF-SAI-001', 'Cliente Exemplo', 'Madeira Serrada 100%', 2, 'm3', 'FSC 100%', 'L-SAI-001', '15', 'entry', 'NF-ENT-001', 'L001', 2, 'Pode informar múltiplas origens separadas por ;'])

        ws3 = wb.create_sheet('Transformacoes')
        ws3.append(['data', 'documento', 'cliente_final', 'produto_origem', 'produto_destino', 'quantidade_produzida', 'unidade_destino', 'id_lote_origem', 'origem_tipo', 'documento_origem', 'lote_origem', 'quantidade_origem', 'observacoes'])
        ws3.append(['2026-03-18', 'TRF-001', 'Cliente Exemplo', 'Toras e Toretes 100%', 'Madeira Serrada 100%', 5, 'm3', '11', 'entry', 'NF-ENT-001', 'L001', 10, 'Informe a produção final; o sistema calcula automaticamente o consumo da origem.'])

        ws4 = wb.create_sheet('Lotes Disponiveis')
        ws4.append(['id_lote', 'tipo_origem', 'uso_permitido', 'documento_origem', 'lote_origem', 'produto', 'saldo_disponivel', 'unidade', 'fornecedor', 'data_origem', 'declaracao_fsc', 'descricao'])

        available_lots = _get_available_import_lots(participant)
        for item in available_lots:
            ws4.append([
                item['id'],
                item['source_type'],
                item['usage_hint'],
                item['document_number'],
                item['batch_code'],
                item['product'],
                float(item['remaining']),
                item['unit'],
                item['supplier'],
                item['movement_date'].strftime('%Y-%m-%d'),
                item['fsc_claim'],
                item['label'],
            ])

        if available_lots:
            last_row = len(available_lots) + 1
            dv = DataValidation(type='list', formula1=f"='Lotes Disponiveis'!$A$2:$A${last_row}", allow_blank=True)
            dv.prompt = 'Selecione um ID de lote listado na aba Lotes Disponiveis.'
            dv.error = 'Escolha um ID de lote válido da aba Lotes Disponiveis.'
            ws2.add_data_validation(dv)
            ws3.add_data_validation(dv)
            dv.add('I2:I500')
            dv.add('H2:H500')

        for ws in [ws1, ws2, ws3, ws4]:
            ws.freeze_panes = 'A2'
            for column_cells in ws.columns:
                max_length = max(len(_safe_str(cell.value)) for cell in column_cells[:50]) if column_cells else 12
                ws.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 28)

        instructions = wb.create_sheet('Instrucoes')
        instructions.append(['Como usar'])
        instructions.append(['1. Para saídas e transformações, consulte a aba Lotes Disponiveis e copie o id_lote para a coluna id_lote_origem.'])
        instructions.append(['2. Para múltiplas origens, separe os IDs e as quantidades por ; nas colunas id_lote_origem e quantidade_origem.'])
        instructions.append(['3. A coluna quantidade_origem deve somar exatamente a quantidade consumida pela linha.'])
        instructions.append(['4. Em transformações, use apenas lotes de entrada.'])
        if participant:
            instructions.append([f'Participante usado para montar os lotes disponíveis: {participant}'])
        else:
            instructions.append(['Selecione um participante na tela antes de baixar o modelo para vir com os lotes disponíveis.'])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=modelo_importacao_fsc.xlsx'
        wb.save(response)
        return response


class ImportWorkbookView(LoginRequiredMixin, View):
    template_name = 'reports/import_workbook.html'

    def _render(self, request, form, preview=None, errors=None, summary=None):
        return render(request, self.template_name, {
            'form': form,
            'preview': preview or {},
            'preview_errors': errors or [],
            'summary': summary or {},
        })

    def get(self, request, *args, **kwargs):
        form = ImportWorkbookForm(initial={'action': 'validate'})
        if not request.user.is_manager:
            form.fields.pop('participant', None)
        return self._render(request, form)

    def post(self, request, *args, **kwargs):
        form = ImportWorkbookForm(request.POST, request.FILES)
        if not request.user.is_manager:
            form.fields.pop('participant', None)
        if not form.is_valid():
            return self._render(request, form)

        participant = form.cleaned_data.get('participant') if request.user.is_manager else request.user.participant
        if not participant:
            messages.error(request, 'Selecione um participante.')
            return self._render(request, form)

        action = request.POST.get('action') or 'validate'
        workbook = openpyxl.load_workbook(form.cleaned_data['workbook'])
        summary, errors, preview = _build_import_preview(workbook, participant, request.user, persist=False)

        if action == 'validate' or errors:
            if errors:
                messages.warning(request, f'Validação concluída com {len(errors)} inconsistências. Corrija a planilha antes de importar.')
            else:
                messages.success(request, 'Validação concluída sem inconsistências. A planilha está pronta para importação.')
            return self._render(request, form, preview=preview, errors=errors, summary=summary)

        # import action
        workbook = openpyxl.load_workbook(form.cleaned_data['workbook'])
        with transaction.atomic():
            summary, errors, preview = _build_import_preview(workbook, participant, request.user, persist=True)
        if errors:
            messages.error(request, 'A importação encontrou inconsistências e não foi concluída por completo. Revise a planilha.')
            return self._render(request, form, preview=preview, errors=errors, summary=summary)

        messages.success(request, f"Importação concluída. Entradas: {summary['entries']}, saídas: {summary['sales']}, transformações: {summary['transformations']}.")
        return redirect('dashboard')
