from django import forms
from .models import MonthlyClosing

class MonthlyClosingForm(forms.ModelForm):
    declaration_text = forms.BooleanField(
        required=True,
        label='Declaro que os dados do período estão completos e corretos.'
    )

    class Meta:
        model = MonthlyClosing
        fields = ['participant_notes', 'declaration_no_movement']
        widgets = {
            'participant_notes': forms.Textarea(attrs={'rows': 4}),
        }
