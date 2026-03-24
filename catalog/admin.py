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
    list_filter = ('type', 'participant__organization')
    search_fields = ('name', 'document_id')
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('participant')
        if request.user.is_superuser: return qs
        org = getattr(request.user, 'current_organization', None)
        return qs.filter(participant__organization=org) if org else qs.none()
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'participant' and not request.user.is_superuser:
            org = getattr(request.user, 'current_organization', None)
            kwargs['queryset'] = db_field.remote_field.model.objects.filter(organization=org) if org else db_field.remote_field.model.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(ProductUnitConversion)
class ProductUnitConversionAdmin(admin.ModelAdmin):
    list_display = ('product', 'from_unit', 'to_unit', 'factor', 'active')
    list_filter = ('from_unit', 'to_unit', 'active')
    search_fields = ('product__name',)

@admin.register(ProductTransformationRule)
class ProductTransformationRuleAdmin(admin.ModelAdmin):
    list_display = ('participant', 'source_product', 'target_product', 'yield_factor', 'active')
    list_filter = ('active', 'participant__organization')
    search_fields = ('source_product__name', 'target_product__name', 'participant__trade_name', 'participant__legal_name')
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('participant', 'source_product', 'target_product')
        if request.user.is_superuser: return qs
        org = getattr(request.user, 'current_organization', None)
        return qs.filter(participant__organization=org) if org else qs.none()
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'participant' and not request.user.is_superuser:
            org = getattr(request.user, 'current_organization', None)
            kwargs['queryset'] = db_field.remote_field.model.objects.filter(organization=org) if org else db_field.remote_field.model.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
