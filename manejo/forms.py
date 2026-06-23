from django import forms
from .models import Especie, Propriedade, InventarioEntrada, SaidaManejo


class EspecieForm(forms.ModelForm):
    class Meta:
        model = Especie
        fields = ['nome', 'fator_m3_para_ton', 'fator_m3_para_st', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Eucalyptus'}),
            'fator_m3_para_ton': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'Ex: 1.04'}),
            'fator_m3_para_st': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'Ex: 1.45'}),
        }


class PropriedadeForm(forms.ModelForm):
    class Meta:
        model = Propriedade
        fields = ['nome', 'codigo', 'municipio', 'uf', 'area_hectares', 'ativa']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Horongozo - Rio Saltinho'}),
            'codigo': forms.TextInput(attrs={'placeholder': 'CAR ou código interno (opcional)'}),
            'municipio': forms.TextInput(attrs={'placeholder': 'Ex: Bituruna'}),
            'uf': forms.TextInput(attrs={'placeholder': 'Ex: PR', 'maxlength': '2'}),
        }


class InventarioEntradaForm(forms.ModelForm):
    class Meta:
        model = InventarioEntrada
        fields = ['propriedade', 'especie', 'data', 'documento', 'volume', 'unidade', 'observacoes', 'attachment']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'volume': forms.NumberInput(attrs={'step': '0.0001'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        self.participant = participant
        if participant:
            self.fields['propriedade'].queryset = Propriedade.objects.filter(participant=participant, ativa=True)
            self.fields['especie'].queryset = Especie.objects.filter(participant=participant, ativo=True)

    def clean(self):
        cleaned = super().clean()
        especie = cleaned.get('especie')
        volume = cleaned.get('volume')
        unidade = cleaned.get('unidade')
        if especie and volume is not None and unidade:
            cleaned['volume_m3'] = especie.converter_para_m3(volume, unidade)
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.participant = self.participant
        instance.volume_m3 = self.cleaned_data['volume_m3']
        if commit:
            instance.save()
        return instance


class SaidaManejoForm(forms.ModelForm):
    class Meta:
        model = SaidaManejo
        fields = ['entrada', 'data', 'documento', 'cliente_nome', 'declaracao_fsc', 'volume', 'unidade', 'observacoes', 'attachment']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'volume': forms.NumberInput(attrs={'step': '0.0001'}),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        self.participant = participant
        if participant:
            entradas = InventarioEntrada.objects.filter(participant=participant).select_related('propriedade', 'especie').com_saldo()
            self.fields['entrada'].queryset = entradas
            self.fields['entrada'].label_from_instance = lambda obj: (
                f"{obj.propriedade.nome} — {obj.especie.nome} (saldo: {obj.saldo_disponivel_m3:.4f} m³)"
            )

    def clean(self):
        cleaned = super().clean()
        entrada = cleaned.get('entrada')
        volume = cleaned.get('volume')
        unidade = cleaned.get('unidade')
        if entrada and volume is not None and unidade:
            volume_m3 = entrada.especie.converter_para_m3(volume, unidade)
            saldo = entrada.saldo_disponivel_m3
            if volume_m3 > saldo:
                raise forms.ValidationError(
                    f'Saldo insuficiente. Disponível: {saldo:.4f} m³. Solicitado: {volume_m3:.4f} m³.'
                )
            cleaned['volume_m3'] = volume_m3
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.participant = self.participant
        instance.volume_m3 = self.cleaned_data['volume_m3']
        if commit:
            instance.save()
        return instance
