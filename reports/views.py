from io import BytesIO
import openpyxl
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from catalog.models import Counterparty, Product
from participants.models import Participant
from transactions.models import EntryRecord, SaleRecord, TransformationRecord
from transactions.services import build_traceability_rows, convert_to_base, calculate_target_from_source, get_transformation_rule, get_entry_balance_rows, sync_entry_lot, reallocate_sale, reallocate_transformation_sources, sync_transformation_target_lot
from .forms import ImportWorkbookForm


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
        ws3.append(['Data', 'Participante', 'Produto origem', 'Qtd origem', 'Unidade origem', 'Qtd origem base', 'Produto destino', 'Qtd destino base', 'Unidade base destino', 'Fator'])
        for obj in TransformationRecord.objects.select_related('participant', 'source_product', 'target_product'):
            ws3.append([obj.movement_date.strftime('%d/%m/%Y'), str(obj.participant), str(obj.source_product), float(obj.source_quantity), obj.source_unit, float(obj.source_quantity_base), str(obj.target_product), float(obj.target_quantity_base), obj.target_unit_snapshot, float(obj.yield_factor_snapshot)])

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


class TraceabilityReportView(ManagerRequiredMixin, View):
    template_name = 'reports/traceability_report.html'

    def get(self, request, *args, **kwargs):
        participant_id = request.GET.get('participant')
        participant = Participant.objects.filter(pk=participant_id).first() if participant_id else None
        rows = build_traceability_rows(participant=participant)
        entry_balances = get_entry_balance_rows(participant=participant)
        return render(request, self.template_name, {'rows': rows, 'entry_balances': entry_balances, 'participants': Participant.objects.filter(status='active'), 'selected_participant': participant})


class ImportTemplateDownloadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = 'Entradas'
        ws1.append(['data', 'documento', 'produto', 'quantidade', 'unidade', 'declaracao_fsc', 'lote', 'observacoes'])
        ws1.append(['2026-03-18', 'NF-ENT-001', 'Toras e Toretes 100%', 10, 't', 'FSC 100%', 'L001', 'Exemplo'])
        ws2 = wb.create_sheet('Saidas')
        ws2.append(['data', 'documento', 'cliente', 'produto', 'quantidade', 'unidade', 'declaracao_fsc', 'lote', 'observacoes'])
        ws2.append(['2026-03-18', 'NF-SAI-001', 'Cliente Exemplo', 'Madeira Serrada 100%', 2, 'm3', 'FSC 100%', 'L001', 'Exemplo'])
        ws3 = wb.create_sheet('Transformacoes')
        ws3.append(['data', 'produto_origem', 'quantidade_origem', 'unidade_origem', 'produto_destino', 'observacoes'])
        ws3.append(['2026-03-18', 'Toras e Toretes 100%', 10, 'm3', 'Madeira Serrada 100%', 'Exemplo'])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=modelo_importacao_fsc.xlsx'
        wb.save(response)
        return response


class ImportWorkbookView(LoginRequiredMixin, View):
    template_name = 'reports/import_workbook.html'

    def get(self, request, *args, **kwargs):
        form = ImportWorkbookForm()
        if not request.user.is_manager:
            form.fields.pop('participant', None)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = ImportWorkbookForm(request.POST, request.FILES)
        if not request.user.is_manager:
            form.fields.pop('participant', None)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        participant = form.cleaned_data.get('participant') if request.user.is_manager else request.user.participant
        if not participant:
            messages.error(request, 'Selecione um participante.')
            return render(request, self.template_name, {'form': form})

        workbook = openpyxl.load_workbook(form.cleaned_data['workbook'])
        created = {'entries': 0, 'sales': 0, 'transformations': 0}

        if 'Entradas' in workbook.sheetnames:
            sheet = workbook['Entradas']
            for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not row[0]:
                    continue
                data, documento, produto_nome, quantidade, unidade, declaracao, lote, observacoes = (list(row) + [None] * 8)[:8]
                product, _ = Product.objects.get_or_create(name=str(produto_nome).strip(), defaults={'unit': unidade or 'm3', 'active': True})
                supplier, _ = Counterparty.objects.get_or_create(participant=participant, name='Não informado', defaults={'type': 'supplier'})
                quantity_base = convert_to_base(product, quantidade, unidade)
                obj = EntryRecord.objects.create(participant=participant, movement_date=data, document_number=str(documento), supplier=supplier, product=product, quantity=quantidade, movement_unit=unidade, unit_snapshot=product.unit, quantity_base=quantity_base, fsc_claim=declaracao or '', batch_code=lote or '', notes=observacoes or '', created_by=request.user, status='submitted')
                sync_entry_lot(obj)
                created['entries'] += 1

        if 'Saidas' in workbook.sheetnames:
            sheet = workbook['Saidas']
            for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not row[0]:
                    continue
                data, documento, cliente_nome, produto_nome, quantidade, unidade, declaracao, lote, observacoes = (list(row) + [None] * 9)[:9]
                product = Product.objects.get(name=str(produto_nome).strip())
                customer, _ = Counterparty.objects.get_or_create(participant=participant, name=str(cliente_nome).strip(), defaults={'type': 'customer'})
                quantity_base = convert_to_base(product, quantidade, unidade)
                obj = SaleRecord.objects.create(participant=participant, movement_date=data, document_number=str(documento), customer=customer, product=product, quantity=quantidade, movement_unit=unidade, unit_snapshot=product.unit, quantity_base=quantity_base, fsc_claim=declaracao or '', batch_code=lote or '', notes=observacoes or '', created_by=request.user, status='submitted')
                reallocate_sale(obj)
                created['sales'] += 1

        if 'Transformacoes' in workbook.sheetnames:
            sheet = workbook['Transformacoes']
            for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not row[0]:
                    continue
                data, produto_origem, quantidade_origem, unidade_origem, produto_destino, observacoes = (list(row) + [None] * 6)[:6]
                source_product = Product.objects.get(name=str(produto_origem).strip())
                target_product = Product.objects.get(name=str(produto_destino).strip())
                source_quantity_base = convert_to_base(source_product, quantidade_origem, unidade_origem)
                target_quantity_base = calculate_target_from_source(source_product, target_product, source_quantity_base)
                rule = get_transformation_rule(source_product, target_product)
                obj = TransformationRecord.objects.create(participant=participant, movement_date=data, source_product=source_product, source_quantity=quantidade_origem, source_unit=unidade_origem, source_quantity_base=source_quantity_base, target_product=target_product, target_quantity_base=target_quantity_base, target_unit_snapshot=target_product.unit, yield_factor_snapshot=rule.yield_factor, notes=observacoes or '', created_by=request.user)
                reallocate_transformation_sources(obj)
                sync_transformation_target_lot(obj)
                created['transformations'] += 1

        messages.success(request, f"Importação concluída. Entradas: {created['entries']}, saídas: {created['sales']}, transformações: {created['transformations']}.")
        return redirect('dashboard')
