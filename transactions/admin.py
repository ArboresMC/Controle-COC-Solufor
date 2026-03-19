from django.contrib import admin
from .models import EntryRecord, SaleRecord, TransformationRecord


@admin.register(EntryRecord)
class EntryRecordAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'document_number', 'product', 'quantity', 'movement_unit', 'quantity_base', 'status')
    list_filter = ('participant', 'status', 'movement_unit')
    search_fields = ('document_number', 'product__name', 'supplier__name')


@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'document_number', 'product', 'quantity', 'movement_unit', 'quantity_base', 'status')
    list_filter = ('participant', 'status', 'movement_unit')
    search_fields = ('document_number', 'product__name', 'customer__name')


@admin.register(TransformationRecord)
class TransformationRecordAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'source_product', 'source_quantity', 'source_unit', 'target_product', 'target_quantity_base')
    list_filter = ('participant', 'source_unit')
    search_fields = ('source_product__name', 'target_product__name')
