from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from .models import Organization, Participant

User = get_user_model()


class OrganizationAdminForm(forms.ModelForm):
    initial_manager_username = forms.CharField(
        label='Username do gestor inicial',
        required=False,
        help_text='Preencha para criar automaticamente o gestor inicial deste ambiente.',
    )
    initial_manager_email = forms.EmailField(
        label='E-mail do gestor inicial',
        required=False,
    )
    initial_manager_password1 = forms.CharField(
        label='Senha provisória',
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )
    initial_manager_password2 = forms.CharField(
        label='Confirmar senha provisória',
        required=False,
        widget=forms.PasswordInput(render_value=True),
    )
    initial_manager_must_change_password = forms.BooleanField(
        label='Obrigar troca de senha no primeiro acesso',
        required=False,
        initial=True,
    )

    class Meta:
        model = Organization
        fields = '__all__'

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip()
        if not slug:
            name = (self.cleaned_data.get('name') or '').strip()
            slug = slugify(name)
        return slug

    def clean(self):
        cleaned = super().clean()
        username = (cleaned.get('initial_manager_username') or '').strip()
        email = (cleaned.get('initial_manager_email') or '').strip()
        password1 = cleaned.get('initial_manager_password1') or ''
        password2 = cleaned.get('initial_manager_password2') or ''

        any_manager_field = any([username, email, password1, password2])
        if any_manager_field:
            missing = []
            if not username:
                missing.append('username do gestor inicial')
            if not email:
                missing.append('e-mail do gestor inicial')
            if not password1:
                missing.append('senha provisória')
            if missing:
                raise forms.ValidationError('Para criar o gestor inicial, preencha: ' + ', '.join(missing) + '.')
            if password1 != password2:
                raise forms.ValidationError('As senhas do gestor inicial não conferem.')
            qs = User.objects.filter(username=username)
            if qs.exists():
                raise forms.ValidationError('Já existe um usuário com esse username.')
        return cleaned


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationAdminForm
    list_display = ('name', 'legal_name', 'slug', 'is_active', 'manager_count', 'participant_count')
    search_fields = ('name', 'legal_name', 'slug')
    list_filter = ('is_active',)

    fieldsets = (
        ('Ambiente', {
            'fields': ('name', 'legal_name', 'slug', 'is_active'),
        }),
        ('Gestor inicial do ambiente', {
            'fields': (
                'initial_manager_username',
                'initial_manager_email',
                'initial_manager_password1',
                'initial_manager_password2',
                'initial_manager_must_change_password',
            ),
            'description': 'Use estes campos somente na criação do ambiente para já nascer com um gestor inicial.',
        }),
    )

    def manager_count(self, obj):
        return obj.users.filter(role='manager').count()

    manager_count.short_description = 'Gestores'

    def participant_count(self, obj):
        return obj.participants.count()

    participant_count.short_description = 'Participantes'

    def save_model(self, request, obj, form, change):
        creating = obj.pk is None
        if not obj.slug:
            obj.slug = slugify(obj.name)
        super().save_model(request, obj, form, change)

        username = (form.cleaned_data.get('initial_manager_username') or '').strip()
        email = (form.cleaned_data.get('initial_manager_email') or '').strip()
        password = form.cleaned_data.get('initial_manager_password1') or ''
        must_change = form.cleaned_data.get('initial_manager_must_change_password', True)

        if creating and username and password:
            user = User(
                username=username,
                email=email,
                role='manager',
                organization=obj,
                must_change_password=must_change,
                is_active=True,
            )
            user.set_password(password)
            user.save()
            self.message_user(
                request,
                f'Ambiente criado com sucesso e gestor inicial "{username}" vinculado.',
                level=messages.SUCCESS,
            )
        elif creating:
            self.message_user(
                request,
                'Ambiente criado com sucesso. Nenhum gestor inicial foi criado.',
                level=messages.SUCCESS,
            )


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('trade_name', 'legal_name', 'organization', 'cnpj', 'status', 'contact_name', 'contact_email')
    search_fields = ('trade_name', 'legal_name', 'cnpj')
    list_filter = ('organization', 'status')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        org = getattr(request.user, 'current_organization', None)
        return qs.filter(organization=org) if org else qs.none()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        org = getattr(request.user, 'current_organization', None)
        if not request.user.is_superuser and 'organization' in form.base_fields:
            form.base_fields['organization'].queryset = form.base_fields['organization'].queryset.filter(id=getattr(org, 'id', None))
            form.base_fields['organization'].initial = org
        return form

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.organization_id:
            obj.organization = request.user.current_organization
        super().save_model(request, obj, form, change)
