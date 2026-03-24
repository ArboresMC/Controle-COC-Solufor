from django.contrib import admin
from .models import Organization, Participant

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'legal_name', 'slug', 'is_active')
    search_fields = ('name', 'legal_name', 'slug')
    list_filter = ('is_active',)

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('trade_name', 'legal_name', 'organization', 'cnpj', 'status', 'contact_name', 'contact_email')
    search_fields = ('trade_name', 'legal_name', 'cnpj')
    list_filter = ('organization', 'status')
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser: return qs
        org = getattr(request.user, 'current_organization', None)
        return qs.filter(organization=org) if org else qs.none()
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs); org = getattr(request.user, 'current_organization', None)
        if not request.user.is_superuser and 'organization' in form.base_fields:
            form.base_fields['organization'].queryset = form.base_fields['organization'].queryset.filter(id=getattr(org, 'id', None)); form.base_fields['organization'].initial = org
        return form
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.organization_id: obj.organization = request.user.current_organization
        super().save_model(request, obj, form, change)
