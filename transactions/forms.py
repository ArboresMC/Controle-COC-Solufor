from django import forms
from decimal import Decimal
from .models import TransformationRecord
from catalog.models import Product
from .models import StockLot
from .services import (
    get_transformation_rule,
    convert_to_base,
    to_decimal,
    get_lot_remaining_for_transformation,
)


class TransformationRecordForm(forms.ModelForm):

    class Meta:
        model = TransformationRecord
        fields = [
            'source_lot',
            'target_product',
            'target_quantity',
            'notes',
        ]

    def __init__(self, *args, **kwargs):
        self.participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)

        if self.participant:
            self.fields['source_lot'].queryset = StockLot.objects.filter(
                participant=self.participant
            )
            self.fields['target_product'].queryset = Product.objects.filter(
                active=True
            )

    def clean(self):
        cleaned = super().clean()

        source_lot = cleaned.get('source_lot')
        target_product = cleaned.get('target_product')
        target_quantity = cleaned.get('target_quantity')

        if not source_lot or not target_product or not target_quantity:
            return cleaned

        try:
            rule = get_transformation_rule(
                source_lot.product,
                target_product,
                participant=self.participant
            )

            if not rule:
                raise ValueError(
                    'Não existe regra de transformação cadastrada para os produtos selecionados.'
                )

            target_quantity_base = convert_to_base(
                target_product,
                target_quantity,
                target_product.unit
            )

            source_quantity_base = (
                to_decimal(target_quantity_base) / to_decimal(rule.yield_factor)
            ).quantize(to_decimal('0.001'))

            cleaned['target_quantity_base'] = target_quantity_base
            cleaned['source_quantity_base'] = source_quantity_base
            cleaned['yield_factor_snapshot'] = to_decimal(rule.yield_factor)

        except Exception as exc:
            self.add_error(None, str(exc))
            return cleaned

        available = get_lot_remaining_for_transformation(
            source_lot,
            transformation=self.instance if getattr(self.instance, 'pk', None) else None,
        )

        if source_quantity_base > available:
            self.add_error(
                'source_lot',
                f'Lote sem saldo suficiente. Disponível: {available}. Necessário: {source_quantity_base}.'
            )

        return cleaned

    def _post_clean(self):
        self.instance.source_product = self.cleaned_data.get('source_lot').product if self.cleaned_data.get('source_lot') else None
        self.instance.source_quantity = self.cleaned_data.get('source_quantity_base')
        self.instance.source_unit = self.cleaned_data.get('source_lot').product.unit if self.cleaned_data.get('source_lot') else None
        self.instance.target_product = self.cleaned_data.get('target_product')
        super()._post_clean()
