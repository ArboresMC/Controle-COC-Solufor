from django import forms
from participants.models import Participant
from .models import Product, Counterparty, ProductUnitConversion, ProductTransformationRule


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit', 'fsc_applicable', 'default_claim', 'active']
        labels = {'unit': 'Unidade base de controle'}


class CounterpartyForm(forms.ModelForm):
    class Meta:
        model = Counterparty
        fields = ['participant', 'name', 'document_id', 'type']


class ProductUnitConversionForm(forms.ModelForm):
    class Meta:
        model = ProductUnitConversion
        fields = ['product', 'from_unit', 'to_unit', 'factor', 'notes', 'active']


class ProductTransformationRuleForm(forms.ModelForm):
    class Meta:
        model = ProductTransformationRule
        fields = ['participant', 'source_product', 'target_product', 'yield_factor', 'notes', 'active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['participant'].queryset = Participant.objects.filter(status='active').order_by('trade_name', 'legal_name')
        self.fields['participant'].required = False
        self.fields['participant'].help_text = 'Selecione a empresa dona do fator. Em branco, a regra vale como padrão geral.'
