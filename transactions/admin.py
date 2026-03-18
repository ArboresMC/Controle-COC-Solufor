from django.contrib import admin
from .models import EntryRecord, SaleRecord

@admin.register(EntryRecord)
class EntryRecordAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'document_number', 'supplier', 'product', 'quantity', 'status')
    list_filter = ('status', 'participant', 'product')
    search_fields = ('document_number', 'supplier__name', 'participant__trade_name', 'participant__legal_name')

@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'document_number', 'customer', 'product', 'quantity', 'status')
    list_filter = ('status', 'participant', 'product')
    search_fields = ('document_number', 'customer__name', 'participant__trade_name', 'participant__legal_name')
