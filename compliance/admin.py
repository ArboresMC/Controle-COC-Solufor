from django.contrib import admin
from .models import MonthlyClosing

@admin.register(MonthlyClosing)
class MonthlyClosingAdmin(admin.ModelAdmin):
    list_display = ('participant', 'month', 'year', 'status', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'year', 'month')
    search_fields = ('participant__trade_name', 'participant__legal_name')
