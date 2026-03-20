from django.contrib import admin
from .models import FSCClaim, Product, Counterparty, ProductUnitConversion, ProductTransformationRule


@admin.register(FSCClaim)
class FSCClaimAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'active', 'sort_order')
    list_filter = ('active',)
    search_fields = ('name', 'code')
    ordering = ('sort_order', 'name')


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


@admin.register(ProductUnitConversion)
class ProductUnitConversionAdmin(admin.ModelAdmin):
    list_display = ('product', 'from_unit', 'to_unit', 'factor', 'active')
    list_filter = ('from_unit', 'to_unit', 'active')
    search_fields = ('product__name',)


@admin.register(ProductTransformationRule)
class ProductTransformationRuleAdmin(admin.ModelAdmin):
    list_display = ('source_product', 'target_product', 'yield_factor', 'active')
    list_filter = ('active',)
    search_fields = ('source_product__name', 'target_product__name')
