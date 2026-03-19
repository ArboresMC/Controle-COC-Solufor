from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Perfil no portal', {'fields': ('role', 'participant', 'must_change_password')}),
    )
    list_display = ('username', 'email', 'role', 'participant', 'is_active')
    list_filter = ('role', 'is_active')
