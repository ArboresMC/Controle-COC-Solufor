from django import forms
from catalog.models import Counterparty, Product
from .models import EntryRecord, SaleRecord


class DateInput(forms.DateInput):
    input_type = 'date'


class BaseMovementForm(forms.ModelForm):
    class Meta:
        fields = [
            'movement_date',
            'document_number',
            'product',
            'quantity',
            'fsc_claim',
            'batch_code',
            'notes',
            'attachment',
        ]
        widgets = {'movement_date': DateInput()}


class EntryRecordForm(BaseMovementForm):
    class Meta(BaseMovementForm.Meta):
        model = EntryRecord
        fields = [
            'movement_date',
            'document_number',
            'supplier',
            'product',
            'quantity',
            'fsc_claim',
            'batch_code',
            'notes',
            'attachment',
        ]

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        qs = Counterparty.objects.filter(type__in=['supplier', 'both'])
        if participant:
            qs = qs.filter(participant__in=[participant, None])
        self.fields['supplier'].queryset = qs.order_by('name')
        self.fields['product'].queryset = Product.objects.filter(active=True).order_by('name')


class SaleRecordForm(BaseMovementForm):
    class Meta(BaseMovementForm.Meta):
        model = SaleRecord
        fields = [
            'movement_date',
            'document_number',
            'customer',
            'product',
            'quantity',
            'fsc_claim',
            'batch_code',
            'notes',
            'attachment',
        ]

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        qs = Counterparty.objects.filter(type__in=['customer', 'both'])
        if participant:
            qs = qs.filter(participant__in=[participant, None])
        self.fields['customer'].queryset = qs.order_by('name')
        self.fields['product'].queryset = Product.objects.filter(active=True).order_by('name')
