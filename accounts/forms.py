from django import forms
from django.contrib.auth.forms import UserCreationForm
from participants.models import Participant
from .models import User


def _participant_label(obj):
    modulos = []
    if obj.ativo_coc:
        modulos.append('CoC')
    if obj.ativo_fm:
        modulos.append('Manejo')
    sufixo = f" [{' + '.join(modulos)}]" if modulos else ' [sem módulo ativo]'
    return f"{obj}{sufixo}"


class UserCreateForm(UserCreationForm):
    participantes_manejo = forms.ModelMultipleChoiceField(
        queryset=Participant.objects.filter(ativo_fm=True, status='active').order_by('trade_name', 'legal_name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Participantes adicionais (Manejo Florestal)',
        help_text='Marque para que este usuário gerencie Manejo Florestal de mais de um participante (não afeta CoC).',
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'participant', 'is_active', 'is_staff'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['participant'].label_from_instance = _participant_label

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.participantes_manejo.set(self.cleaned_data.get('participantes_manejo', []))
        return user


class UserUpdateForm(forms.ModelForm):
    new_password = forms.CharField(
        label='Nova senha (opcional)',
        required=False,
        widget=forms.PasswordInput(render_value=False)
    )
    participantes_manejo = forms.ModelMultipleChoiceField(
        queryset=Participant.objects.filter(ativo_fm=True, status='active').order_by('trade_name', 'legal_name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Participantes adicionais (Manejo Florestal)',
        help_text='Marque para que este usuário gerencie Manejo Florestal de mais de um participante (não afeta CoC).',
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'participant', 'is_active', 'is_staff'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['participant'].label_from_instance = _participant_label
        if self.instance.pk:
            self.fields['participantes_manejo'].initial = self.instance.participantes_manejo.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
            user.participantes_manejo.set(self.cleaned_data.get('participantes_manejo', []))
        return user
