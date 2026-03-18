import openpyxl
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.utils import timezone
from django.views import View
from transactions.models import EntryRecord, SaleRecord

class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager

class ConsolidatedExcelReportView(ManagerRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = 'Entradas'
        ws1.append(['Data', 'Participante', 'Documento', 'Fornecedor', 'Produto', 'Quantidade', 'Unidade', 'Declaração FSC', 'Status'])
        for obj in EntryRecord.objects.select_related('participant', 'supplier', 'product'):
            ws1.append([
                obj.movement_date.strftime('%d/%m/%Y'),
                str(obj.participant),
                obj.document_number,
                str(obj.supplier),
                str(obj.product),
                float(obj.quantity),
                obj.unit_snapshot,
                obj.fsc_claim,
                obj.get_status_display(),
            ])
        ws2 = wb.create_sheet('Saídas')
        ws2.append(['Data', 'Participante', 'Documento', 'Cliente', 'Produto', 'Quantidade', 'Unidade', 'Declaração FSC', 'Status'])
        for obj in SaleRecord.objects.select_related('participant', 'customer', 'product'):
            ws2.append([
                obj.movement_date.strftime('%d/%m/%Y'),
                str(obj.participant),
                obj.document_number,
                str(obj.customer),
                str(obj.product),
                float(obj.quantity),
                obj.unit_snapshot,
                obj.fsc_claim,
                obj.get_status_display(),
            ])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f'relatorio_fsc_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        wb.save(response)
        return response
