from django.urls import path
from .views import (
    AuditPdfReportView,
    ConsolidatedExcelReportView,
    ImportErrorsDownloadView,
    ImportTemplateDownloadView,
    ImportWorkbookView,
    TraceabilityReportView,
)

urlpatterns = [
    path('consolidated.xlsx', ConsolidatedExcelReportView.as_view(), name='report_consolidated_excel'),
    path('audit.pdf', AuditPdfReportView.as_view(), name='report_audit_pdf'),
    path('traceability/', TraceabilityReportView.as_view(), name='report_traceability'),
    path('import/', ImportWorkbookView.as_view(), name='report_import_workbook'),
    path('import-template.xlsx', ImportTemplateDownloadView.as_view(), name='report_import_template'),
    path('import-errors/<int:job_id>.xlsx', ImportErrorsDownloadView.as_view(), name='report_import_errors_download'),
]
