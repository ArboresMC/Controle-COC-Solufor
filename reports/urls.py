from django.urls import path
from .views import (
    AuditPdfReportView,
    ConsolidatedExcelReportView,
    ImportTemplateDownloadView,
    ImportWorkbookView,
    TraceabilityReportView,
    import_job_status,
)

urlpatterns = [
    path('consolidated.xlsx', ConsolidatedExcelReportView.as_view(), name='report_consolidated_excel'),
    path('audit.pdf', AuditPdfReportView.as_view(), name='report_audit_pdf'),
    path('traceability/', TraceabilityReportView.as_view(), name='report_traceability'),
    path('import/', ImportWorkbookView.as_view(), name='report_import_workbook'),
    path('import/status/<int:job_id>/', import_job_status, name='report_import_job_status'),
    path('import-template.xlsx', ImportTemplateDownloadView.as_view(), name='report_import_template'),
]
