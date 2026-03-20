from django.contrib import admin
from .models import EntryRecord, SaleRecord, TransformationRecord, TraceLot, LotAllocation


@admin.register(EntryRecord)
class EntryRecordAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'document_number', 'supplier', 'product', 'quantity', 'movement_unit', 'quantity_base', 'status')
    list_filter = ('participant', 'status', 'movement_unit')
    search_fields = ('document_number', 'product__name', 'supplier__name')


@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'document_number', 'customer', 'product', 'quantity', 'movement_unit', 'quantity_base', 'status')
    list_filter = ('participant', 'status', 'movement_unit')
    search_fields = ('document_number', 'product__name', 'customer__name')


@admin.register(TransformationRecord)
class TransformationRecordAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'document_number', 'customer', 'supplier', 'fsc_claim', 'source_product', 'target_product', 'target_quantity_base')
    list_filter = ('participant', 'source_unit')
    search_fields = ('document_number', 'source_product__name', 'target_product__name', 'customer__name')


@admin.register(TraceLot)
class TraceLotAdmin(admin.ModelAdmin):
    list_display = ('movement_date', 'participant', 'product', 'source_type', 'supplier', 'quantity_base')
    list_filter = ('participant', 'product', 'source_type')
    search_fields = ('entry__document_number', 'transformation__id', 'product__name', 'supplier__name')


@admin.register(LotAllocation)
class LotAllocationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'lot', 'target_type', 'sale', 'transformation', 'quantity_base', 'created_at')
    list_filter = ('participant', 'target_type')
    search_fields = ('lot__entry__document_number', 'sale__document_number', 'lot__supplier__name')
