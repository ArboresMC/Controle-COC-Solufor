from django import forms
from catalog.models import Counterparty, Product
from .models import EntryRecord, SaleRecord, TransformationRecord
from .services import calculate_target_from_source, convert_to_base


class DateInput(forms.DateInput):
    input_type = 'date'


UNIT_CHOICES = Product.UNIT_CHOICES


class BaseMovementForm(forms.ModelForm):
    movement_unit = forms.ChoiceField(label='Unidade', choices=UNIT_CHOICES)

    class Meta:
        fields = [
            'movement_date',
            'document_number',
            'product',
            'quantity',
            'movement_unit',
            'fsc_claim',
            'batch_code',
            'notes',
            'attachment',
        ]
        widgets = {'movement_date': DateInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, 'pk', None) and self.instance.movement_unit:
            self.fields['movement_unit'].initial = self.instance.movement_unit
        elif self.instance and getattr(self.instance, 'pk', None) and self.instance.product_id:
            self.fields['movement_unit'].initial = self.instance.product.unit

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        quantity = cleaned.get('quantity')
        movement_unit = cleaned.get('movement_unit')
        if product and quantity and movement_unit:
            try:
                cleaned['quantity_base'] = convert_to_base(product, quantity, movement_unit)
            except Exception as exc:
                self.add_error('movement_unit', str(exc))
        return cleaned


class EntryRecordForm(BaseMovementForm):
    class Meta(BaseMovementForm.Meta):
        model = EntryRecord
        fields = BaseMovementForm.Meta.fields

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(active=True).order_by('name')
        self.participant = participant


class SaleRecordForm(BaseMovementForm):
    class Meta(BaseMovementForm.Meta):
        model = SaleRecord
        fields = [
            'movement_date',
            'document_number',
            'customer',
            'product',
            'quantity',
            'movement_unit',
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


class TransformationRecordForm(forms.ModelForm):
    source_unit = forms.ChoiceField(label='Unidade origem', choices=UNIT_CHOICES)

    class Meta:
        model = TransformationRecord
        fields = [
            'movement_date',
            'source_product',
            'source_quantity',
            'source_unit',
            'target_product',
            'notes',
            'attachment',
        ]
        widgets = {'movement_date': DateInput()}

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        self.fields['source_product'].queryset = Product.objects.filter(active=True).order_by('name')
        self.fields['target_product'].queryset = Product.objects.filter(active=True).order_by('name')
        if self.instance and getattr(self.instance, 'pk', None):
            self.fields['source_unit'].initial = self.instance.source_unit
        self.participant = participant

    def clean(self):
        cleaned = super().clean()
        source_product = cleaned.get('source_product')
        source_quantity = cleaned.get('source_quantity')
        source_unit = cleaned.get('source_unit')
        target_product = cleaned.get('target_product')
        if source_product and source_quantity and source_unit and target_product:
            try:
                source_quantity_base = convert_to_base(source_product, source_quantity, source_unit)
                target_quantity_base = calculate_target_from_source(source_product, target_product, source_quantity_base)
                cleaned['source_quantity_base'] = source_quantity_base
                cleaned['target_quantity_base'] = target_quantity_base
            except Exception as exc:
                self.add_error(None, str(exc))
        return cleaned
