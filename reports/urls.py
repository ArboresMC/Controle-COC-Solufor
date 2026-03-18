from django.urls import path
from .views import ConsolidatedExcelReportView

urlpatterns = [
    path('consolidated.xlsx', ConsolidatedExcelReportView.as_view(), name='report_consolidated_excel'),
]
