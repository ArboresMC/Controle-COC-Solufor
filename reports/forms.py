from django import forms
from participants.models import Participant


class ImportWorkbookForm(forms.Form):
    participant = forms.ModelChoiceField(queryset=Participant.objects.filter(status='active').order_by('trade_name', 'legal_name'), required=False, label='Participante')
    workbook = forms.FileField(label='Planilha Excel')
