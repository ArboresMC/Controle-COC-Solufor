from django import forms
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
        fields = ['source_product', 'target_product', 'yield_factor', 'notes', 'active']
