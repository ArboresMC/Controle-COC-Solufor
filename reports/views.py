from decimal import Decimal
from unicodedata import normalize

from django.core.files.base import File
from django.db import transaction
from io import BytesIO
from pathlib import Path

import openpyxl
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views import View

from catalog.models import Counterparty, Product
from participants.models import Participant
from transactions.models import EntryRecord, SaleRecord, TransformationRecord
from transactions.services import (
    build_traceability_rows,
    calculate_target_from_source,
    convert_to_base,
    get_entry_balance_rows,
    get_transformation_rule,
    reallocate_sale,
    reallocate_transformation_sources,
    sync_entry_lot,
    sync_transformation_target_lot,
)
from .forms import ImportWorkbookForm
from .models import ImportJob


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


def _build_import_preview(workbook, participant, user, persist=False, progress_callback=None):
    summary = {'entries': 0, 'sales': 0, 'transformations': 0}
    errors = []
    previews = {'entries': [], 'sales': [], 'transformations': []}

    total_rows = 0
    for sheet_name in ('Entradas', 'Saidas', 'Transformacoes'):
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            total_rows += sum(1 for _idx, _row in _sheet_rows(sheet))
    processed_rows = 0

    if progress_callback:
        progress_callback(processed_rows, total_rows)

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
            finally:
                processed_rows += 1
                if progress_callback:
                    progress_callback(processed_rows, total_rows)

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
                preview = {
                    'linha': idx,
                    'data': data,
                    'documento': _safe_str(documento),
                    'customer': customer_name,
                    'product': product.name,
                    'quantity': quantidade,
                    'unit': unidade,
                    'quantity_base': quantity_base,
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
                    reallocate_sale(obj)
            except Exception as exc:
                errors.append(f'Saidas linha {idx}: {exc}')
            finally:
                processed_rows += 1
                if progress_callback:
                    progress_callback(processed_rows, total_rows)

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
                    reallocate_transformation_sources(obj)
                    sync_transformation_target_lot(obj)
            except Exception as exc:
                errors.append(f'Transformacoes linha {idx}: {exc}')
            finally:
                processed_rows += 1
                if progress_callback:
                    progress_callback(processed_rows, total_rows)

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


def _serialize_preview(preview):
    def _serialize_row(row):
        payload = {}
        for key, value in row.items():
            if hasattr(value, 'isoformat'):
                payload[key] = value.isoformat()
            else:
                payload[key] = str(value) if isinstance(value, Decimal) else value
        return payload

    return {
        'entries': [_serialize_row(row) for row in preview.get('entries', [])[:100]],
        'sales': [_serialize_row(row) for row in preview.get('sales', [])[:100]],
        'transformations': [_serialize_row(row) for row in preview.get('transformations', [])[:100]],
    }


def process_import_job(job):
    def _heartbeat(current, total):
        ImportJob.objects.filter(pk=job.pk).update(
            progress_current=current,
            progress_total=total,
            last_heartbeat=timezone.now(),
        )

    now = timezone.now()
    ImportJob.objects.filter(pk=job.pk).update(
        status=ImportJob.STATUS_PROCESSING,
        started_at=now,
        last_heartbeat=now,
        error_messages=[],
    )

    try:
        with job.workbook.open('rb') as fh:
            workbook = openpyxl.load_workbook(fh)
            with transaction.atomic():
                summary, errors, preview = _build_import_preview(
                    workbook,
                    job.participant,
                    job.created_by,
                    persist=True,
                    progress_callback=_heartbeat,
                )

        status = ImportJob.STATUS_COMPLETED if not errors else ImportJob.STATUS_FAILED
        refreshed = ImportJob.objects.get(pk=job.pk)
        ImportJob.objects.filter(pk=job.pk).update(
            status=status,
            summary=summary,
            error_messages=errors,
            preview=_serialize_preview(preview),
            finished_at=timezone.now(),
            last_heartbeat=timezone.now(),
            progress_current=refreshed.progress_total or refreshed.progress_current,
        )
    except Exception as exc:
        ImportJob.objects.filter(pk=job.pk).update(
            status=ImportJob.STATUS_FAILED,
            error_messages=[str(exc)],
            finished_at=timezone.now(),
            last_heartbeat=timezone.now(),
        )
        raise


@require_GET
def import_job_status(request, job_id):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'Autenticação necessária.'}, status=403)

    job = get_object_or_404(ImportJob.objects.select_related('participant', 'created_by'), pk=job_id)
    if (not request.user.is_manager) and job.created_by_id != request.user.id:
        return JsonResponse({'detail': 'Acesso negado.'}, status=403)

    return JsonResponse({
        'id': job.id,
        'status': job.status,
        'status_label': job.get_status_display(),
        'summary': job.summary or {},
        'errors': job.error_messages or [],
        'progress_current': job.progress_current,
        'progress_total': job.progress_total,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'finished_at': job.finished_at.isoformat() if job.finished_at else None,
        'participant': str(job.participant),
        'original_filename': job.original_filename,
    })


class ImportTemplateDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = 'Entradas'
        ws1.append(['data', 'documento', 'fornecedor', 'produto', 'quantidade', 'unidade', 'declaracao_fsc', 'lote', 'observacoes'])
        ws1.append(['2026-03-18', 'NF-ENT-001', 'Fornecedor Exemplo', 'Toras e Toretes 100%', 10, 't', 'FSC 100%', 'L001', 'Exemplo'])
        ws2 = wb.create_sheet('Saidas')
        ws2.append(['data', 'documento', 'cliente', 'produto', 'quantidade', 'unidade', 'declaracao_fsc', 'lote', 'observacoes'])
        ws2.append(['2026-03-18', 'NF-SAI-001', 'Cliente Exemplo', 'Madeira Serrada 100%', 2, 'm3', 'FSC 100%', 'L001', 'Exemplo'])
        ws3 = wb.create_sheet('Transformacoes')
        ws3.append(['data', 'documento', 'cliente_final', 'produto_origem', 'produto_destino', 'quantidade_produzida', 'unidade_destino', 'observacoes'])
        ws3.append(['2026-03-18', 'TRF-001', 'Cliente Exemplo', 'Toras e Toretes 100%', 'Madeira Serrada 100%', 5, 'm3', 'Informe a produção final; o sistema calcula automaticamente o consumo da origem.'])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=modelo_importacao_fsc.xlsx'
        wb.save(response)
        return response


class ImportWorkbookView(LoginRequiredMixin, View):
    template_name = 'reports/import_workbook.html'

    def _render(self, request, form, preview=None, errors=None, summary=None, import_job=None):
        return render(request, self.template_name, {
            'form': form,
            'preview': preview or {},
            'preview_errors': errors or [],
            'summary': summary or {},
            'import_job': import_job,
        })

    def get(self, request, *args, **kwargs):
        form = ImportWorkbookForm(initial={'action': 'validate'})
        if not request.user.is_manager:
            form.fields.pop('participant', None)
        import_job = ImportJob.objects.filter(created_by=request.user).order_by('-created_at').first()
        return self._render(request, form, import_job=import_job)

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
        workbook_file = form.cleaned_data['workbook']

        if action == 'validate':
            workbook = openpyxl.load_workbook(workbook_file)
            summary, errors, preview = _build_import_preview(workbook, participant, request.user, persist=False)
            if errors:
                messages.warning(request, f'Validação concluída com {len(errors)} inconsistências. Corrija a planilha antes de importar.')
            else:
                messages.success(request, 'Validação concluída sem inconsistências. A planilha está pronta para importação.')
            return self._render(request, form, preview=preview, errors=errors, summary=summary)

        workbook = openpyxl.load_workbook(workbook_file)
        summary, errors, preview = _build_import_preview(workbook, participant, request.user, persist=False)
        if errors:
            messages.error(request, 'A importação não foi enfileirada porque a validação encontrou inconsistências. Corrija a planilha e tente novamente.')
            return self._render(request, form, preview=preview, errors=errors, summary=summary)

        workbook_file.seek(0)
        import_job = ImportJob.objects.create(
            participant=participant,
            created_by=request.user,
            original_filename=Path(workbook_file.name).name,
            summary=summary,
            preview=_serialize_preview(preview),
        )
        import_job.workbook.save(Path(workbook_file.name).name, File(workbook_file), save=True)

        messages.success(request, 'Importação enviada para a fila interna. Você pode acompanhar o progresso nesta tela sem travar o sistema.')
        fresh_form = ImportWorkbookForm(initial={'action': 'validate'})
        if not request.user.is_manager:
            fresh_form.fields.pop('participant', None)
        return self._render(request, fresh_form, import_job=import_job)
