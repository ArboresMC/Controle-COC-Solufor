from django.urls import path
from .views import ConsolidatedExcelReportView, TraceabilityReportView, ImportTemplateDownloadView, ImportWorkbookView

urlpatterns = [
    path('consolidated.xlsx', ConsolidatedExcelReportView.as_view(), name='report_consolidated_excel'),
    path('traceability/', TraceabilityReportView.as_view(), name='report_traceability'),
    path('import/', ImportWorkbookView.as_view(), name='report_import_workbook'),
    path('import-template.xlsx', ImportTemplateDownloadView.as_view(), name='report_import_template'),
]
