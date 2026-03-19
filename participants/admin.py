from django.contrib import admin
from .models import Participant

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('trade_name', 'legal_name', 'cnpj', 'status', 'contact_name', 'contact_email')
    search_fields = ('trade_name', 'legal_name', 'cnpj')
    list_filter = ('status',)
