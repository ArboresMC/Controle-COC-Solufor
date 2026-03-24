from django.contrib import admin
from .models import MonthlyClosing

@admin.register(MonthlyClosing)
class MonthlyClosingAdmin(admin.ModelAdmin):
    list_display = ('participant', 'month', 'year', 'status', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'year', 'month', 'participant__organization')
    search_fields = ('participant__trade_name', 'participant__legal_name')
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('participant', 'reviewed_by')
        if request.user.is_superuser: return qs
        org = getattr(request.user, 'current_organization', None)
        return qs.filter(participant__organization=org) if org else qs.none()
