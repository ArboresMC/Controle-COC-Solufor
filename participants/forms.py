from django import forms
from .models import Participant


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            'legal_name', 'trade_name', 'cnpj', 'contact_name',
            'contact_email', 'contact_phone', 'status'
        ]
