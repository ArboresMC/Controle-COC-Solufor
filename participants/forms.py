from django import forms
from .models import Participant


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            'legal_name', 'trade_name', 'cnpj', 'contact_name',
            'contact_email', 'contact_phone', 'status',
            'ativo_coc', 'ativo_fm',
        ]
        labels = {
            'ativo_coc': 'Módulo Cadeia de Custódia (CoC)',
            'ativo_fm': 'Módulo Manejo Florestal (FM)',
        }
        help_texts = {
            'ativo_coc': 'Habilita lançamentos de entrada, saída e transformação FSC.',
            'ativo_fm': 'Habilita o inventário de manejo florestal.',
        }
