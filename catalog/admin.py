from django.contrib import admin
from .models import Product, Counterparty

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'fsc_applicable', 'active')
    list_filter = ('category', 'fsc_applicable', 'active')
    search_fields = ('name',)

@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'participant', 'document_id')
    list_filter = ('type',)
    search_fields = ('name', 'document_id')
