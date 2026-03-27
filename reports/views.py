from decimal import Decimal
from unicodedata import normalize

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator

import openpyxl
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View

from catalog.models import Counterparty, Product
from participants.models import Participant
from transactions.models import EntryRecord, SaleRecord, TransformationRecord
from transactions.performance import build_cache_key
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
from .services import (
build_import_error_workbook,
    build_import_preview,
    count_workbook_rows,
    humanize_import_errors,

)


def _serialize_json_safe(value):
    if isinstance(value, dict):
        return {key: _serialize_json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_json_safe(item) for item in value]
    if hasattr(value, 'isoformat'):
        try:
            return value.isoformat()
        except Exception:
            pass
    if isinstance(value, Decimal):
        return str(value)
    return value



class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager



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
        current_org = getattr(request.user, 'current_organization', None)
        scope_type = 'organization' if (request.user.is_manager or request.user.is_auditor) else 'participant'
        scope_id = getattr(current_org, 'id', None) if scope_type == 'organization' else getattr(getattr(request.user, 'participant', None), 'id', None)
        cache_extra = f"traceability:{participant_id or 'all'}"
        cache_key = build_cache_key('report', scope_type, scope_id, extra=cache_extra)
        cached = cache.get(cache_key)
        if cached is None:
            rows = build_traceability_rows(participant=participant)
            entry_balances = get_entry_balance_rows(participant=participant)
            participants = list(Participant.objects.filter(status='active'))
            cached = {'rows': rows, 'entry_balances': entry_balances, 'participants': participants}
            cache.set(cache_key, cached, settings.CACHE_TTL_TRACEABILITY)

        rows_paginator = Paginator(cached['rows'], 80)
        balances_paginator = Paginator(cached['entry_balances'], 80)
        rows_page = rows_paginator.get_page(request.GET.get('page'))
        balances_page = balances_paginator.get_page(request.GET.get('balance_page'))
        query_for_rows = request.GET.copy()
        query_for_rows.pop('page', None)
        query_for_balances = request.GET.copy()
        query_for_balances.pop('balance_page', None)

        return render(request, self.template_name, {
            'rows': rows_page,
            'entry_balances': balances_page,
            'participants': cached['participants'],
            'selected_participant': participant,
            'rows_page_obj': rows_page,
            'balances_page_obj': balances_page,
            'rows_query_string': query_for_rows.urlencode(),
            'balances_query_string': query_for_balances.urlencode(),
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


class ImportErrorsDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        job = _get_visible_import_job(request, kwargs.get('job_id'))
        if not job or not job.error_messages:
            messages.warning(request, 'Nenhum relatório de erros disponível para este job.')
            return redirect('report_import_workbook')

        wb = build_import_error_workbook(job.error_messages)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f'erros_importacao_job_{job.pk}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        wb.save(response)
        return response


def _get_import_jobs_queryset(request):
    qs = ImportJob.objects.select_related('participant', 'created_by').order_by('-created_at', '-id')
    if request.user.is_manager or request.user.is_auditor:
        current_org = getattr(request.user, 'current_organization', None)
        if current_org:
            qs = qs.filter(participant__organization=current_org)
        return qs
    if getattr(request.user, 'participant_id', None):
        return qs.filter(participant=request.user.participant)
    return qs.none()


def _get_visible_import_job(request, job_id):
    if not job_id:
        return None
    return _get_import_jobs_queryset(request).filter(pk=job_id).first()



class ImportWorkbookView(LoginRequiredMixin, View):
    template_name = 'reports/import_workbook.html'

    def _build_form(self, request, *args, **kwargs):
        form = ImportWorkbookForm(*args, **kwargs)
        if request.user.is_manager:
            current_org = getattr(request.user, 'current_organization', None)
            if current_org:
                form.fields['participant'].queryset = form.fields['participant'].queryset.filter(organization=current_org)
        else:
            form.fields.pop('participant', None)
        return form

    def _render(self, request, form, preview=None, errors=None, summary=None, selected_job=None):
        jobs = list(_get_import_jobs_queryset(request)[:15])
        if not selected_job and jobs:
            requested_job_id = request.GET.get('job')
            selected_job = _get_visible_import_job(request, requested_job_id) if requested_job_id else jobs[0]
        return render(request, self.template_name, {
            'form': form,
            'preview': preview or {},
            'preview_errors': humanize_import_errors(errors or []),
            'summary': summary or {},
            'jobs': jobs,
            'selected_job': selected_job,
            'selected_job_error_url': reverse('report_import_errors_download', kwargs={'job_id': selected_job.pk}) if selected_job and selected_job.error_messages else '',
            'is_job_running': bool(selected_job and selected_job.status in [ImportJob.STATUS_PENDING, ImportJob.STATUS_PROCESSING]),
            'import_mode': getattr(settings, 'IMPORT_MODE', 'sync'),
        })

    def get(self, request, *args, **kwargs):
        form = self._build_form(request, initial={'action': 'validate'})
        selected_job = _get_visible_import_job(request, request.GET.get('job'))
        return self._render(request, form, selected_job=selected_job)

    def post(self, request, *args, **kwargs):
        form = self._build_form(request, request.POST, request.FILES)
        if not form.is_valid():
            return self._render(request, form)

        participant = form.cleaned_data.get('participant') if request.user.is_manager else request.user.participant
        if not participant:
            messages.error(request, 'Selecione um participante.')
            return self._render(request, form)

        action = request.POST.get('action') or 'validate'
        uploaded_file = form.cleaned_data['workbook']
        workbook = openpyxl.load_workbook(uploaded_file)
        summary, errors, preview = build_import_preview(workbook, participant, request.user, persist=False)

        if action == 'validate' or errors:
            if errors:
                messages.warning(request, f'Validação concluída com {len(errors)} inconsistências. Corrija a planilha antes de importar.')
            else:
                messages.success(request, 'Validação concluída sem inconsistências. A planilha está pronta para importação.')
            return self._render(request, form, preview=preview, errors=errors, summary=summary)

        import_mode = getattr(settings, 'IMPORT_MODE', 'sync')

        if import_mode == 'sync':
            uploaded_file.seek(0)
            workbook = openpyxl.load_workbook(uploaded_file)
            summary, errors, preview = build_import_preview(workbook, participant, request.user, persist=True)

            if errors:
                messages.error(request, 'A importação encontrou inconsistências e não foi concluída por completo. Revise a planilha.')
                return self._render(request, form, preview=preview, errors=errors, summary=summary)

            messages.success(
                request,
                f"Importação concluída. Entradas: {summary.get('entries', 0)}, saídas: {summary.get('sales', 0)}, transformações: {summary.get('transformations', 0)}."
            )
            return redirect('dashboard')

        uploaded_file.seek(0)
        total_rows = count_workbook_rows(workbook)
        job = ImportJob.objects.create(
            participant=participant,
            created_by=request.user,
            workbook=uploaded_file,
            original_filename=getattr(uploaded_file, 'name', ''),
            status=ImportJob.STATUS_PENDING,
            summary=_serialize_json_safe(summary),
            preview=_serialize_json_safe(preview),
            error_messages=[],
            progress_current=0,
            progress_total=total_rows,
        )
        messages.success(request, f'Importação enviada para a fila com sucesso. Job #{job.pk} criado para {job.original_filename or "planilha"}.')
        return redirect(f"{reverse('report_import_workbook')}?job={job.pk}")

