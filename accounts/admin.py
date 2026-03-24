from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Perfil no portal', {'fields': ('role', 'organization', 'participant', 'must_change_password')}),
    )
    list_display = ('username', 'email', 'role', 'organization', 'participant', 'is_active')
    list_filter = ('role', 'organization', 'is_active')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        org = getattr(request.user, 'current_organization', None)
        return qs.filter(organization=org) if org else qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        org = getattr(request.user, 'current_organization', None)
        if not request.user.is_superuser:
            if 'organization' in form.base_fields:
                form.base_fields['organization'].queryset = form.base_fields['organization'].queryset.filter(id=getattr(org, 'id', None))
                form.base_fields['organization'].initial = org
            if 'participant' in form.base_fields:
                form.base_fields['participant'].queryset = form.base_fields['participant'].queryset.filter(organization=org)
        return form

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            if obj.participant_id and obj.participant and obj.participant.organization_id:
                obj.organization = obj.participant.organization
            elif not obj.organization_id:
                obj.organization = request.user.current_organization
        super().save_model(request, obj, form, change)
