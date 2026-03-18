from django import forms
from .models import Product, Counterparty


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit', 'fsc_applicable', 'default_claim', 'active']


class CounterpartyForm(forms.ModelForm):
    class Meta:
        model = Counterparty
        fields = ['participant', 'name', 'document_id', 'type']
