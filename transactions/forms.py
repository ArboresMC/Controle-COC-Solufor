from django import forms
from catalog.models import Counterparty, Product
from .models import EntryRecord, SaleRecord, TransformationRecord, TraceLot
from .services import calculate_target_from_source, convert_to_base, get_lot_remaining_for_sale, get_manual_sale_lot_choices


class DateInput(forms.DateInput):
    input_type = 'date'


UNIT_CHOICES = Product.UNIT_CHOICES


class BaseMovementForm(forms.ModelForm):
    movement_unit = forms.ChoiceField(label='Unidade', choices=UNIT_CHOICES)
    new_product_name = forms.CharField(label='Novo produto (opcional)', required=False)

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
        self.fields['new_product_name'].help_text = 'Se informado, cria o produto usando a unidade selecionada como unidade base.'

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        quantity = cleaned.get('quantity')
        movement_unit = cleaned.get('movement_unit')
        new_product_name = (cleaned.get('new_product_name') or '').strip()
        if new_product_name and movement_unit and not product:
            cleaned['new_product_payload'] = {
                'name': new_product_name,
                'unit': movement_unit,
            }
        if product and quantity and movement_unit:
            try:
                cleaned['quantity_base'] = convert_to_base(product, quantity, movement_unit)
            except Exception as exc:
                self.add_error('movement_unit', str(exc))
        return cleaned


class EntryRecordForm(BaseMovementForm):
    class Meta(BaseMovementForm.Meta):
        model = EntryRecord
        fields = [
            'movement_date',
            'document_number',
            'supplier',
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
        self.fields['product'].queryset = Product.objects.filter(active=True).order_by('name')
        supplier_qs = Counterparty.objects.filter(type__in=['supplier', 'both'])
        if participant:
            supplier_qs = supplier_qs.filter(participant__in=[participant, None])
        self.fields['supplier'].queryset = supplier_qs.order_by('name')
        self.fields['supplier'].required = False
        self.fields['supplier'].help_text = 'Selecione o fornecedor da entrada. Em branco, o sistema usará “Não informado”.'
        self.participant = participant


class SaleRecordForm(BaseMovementForm):
    new_customer_name = forms.CharField(label='Novo cliente (opcional)', required=False)
    source_lot = forms.ModelChoiceField(label='Alocação manual da origem (opcional)', queryset=TraceLot.objects.none(), required=False, empty_label='Usar FIFO automático')
    supplier = forms.ModelChoiceField(
        label='Fornecedor de origem',
        queryset=Counterparty.objects.none(),
        required=False,
        disabled=True,
    )

    class Meta(BaseMovementForm.Meta):
        model = SaleRecord
        fields = [
            'movement_date',
            'document_number',
            'customer',
            'supplier',
            'product',
            'quantity',
            'movement_unit',
            'fsc_claim',
            'batch_code',
            'notes',
            'attachment',
            'source_lot',
        ]

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        self.participant = participant
        qs = Counterparty.objects.filter(type__in=['customer', 'both'])
        if participant:
            qs = qs.filter(participant__in=[participant, None])
        self.fields['customer'].queryset = qs.order_by('name')
        supplier_qs = Counterparty.objects.filter(type__in=['supplier', 'both'])
        if participant:
            supplier_qs = supplier_qs.filter(participant__in=[participant, None])
        self.fields['supplier'].queryset = supplier_qs.order_by('name')
        self.fields['product'].queryset = Product.objects.filter(active=True).order_by('name')
        self.fields['new_customer_name'].help_text = 'Se informado, cria um novo cliente para este participante.'
        self.fields['source_lot'].help_text = 'Opcional: selecione um lote específico para vincular a venda a uma compra ou transformação determinada. Em branco, o sistema usa FIFO automático.'
        self.fields['supplier'].help_text = 'O fornecedor é herdado automaticamente do lote de origem e não pode ser alterado na saída.'

        selected_product = None
        if self.is_bound:
            product_value = self.data.get('product')
            if product_value:
                try:
                    selected_product = Product.objects.get(pk=product_value)
                except Product.DoesNotExist:
                    selected_product = None
        elif self.instance and getattr(self.instance, 'product_id', None):
            selected_product = self.instance.product

        selected_claim = None
        if self.is_bound:
            selected_claim = (self.data.get('fsc_claim') or '').strip() or None
        elif self.instance and getattr(self.instance, 'fsc_claim', ''):
            selected_claim = self.instance.fsc_claim

        if participant:
            lot_choices = get_manual_sale_lot_choices(
                participant,
                product=selected_product,
                sale=self.instance if getattr(self.instance, 'pk', None) else None,
                fsc_claim=selected_claim,
            )
            lot_ids = [item['lot'].id for item in lot_choices]
            self.fields['source_lot'].queryset = TraceLot.objects.filter(pk__in=lot_ids).select_related('product', 'supplier', 'entry', 'transformation').order_by('movement_date', 'id')
            self.available_lot_choices = lot_choices
        else:
            self.available_lot_choices = []

        supplier_initial = None
        if self.is_bound:
            source_lot_id = self.data.get('source_lot')
            if source_lot_id:
                try:
                    source_lot = TraceLot.objects.select_related('supplier').get(pk=source_lot_id)
                    supplier_initial = source_lot.supplier
                except TraceLot.DoesNotExist:
                    supplier_initial = None
        elif self.instance and getattr(self.instance, 'supplier_id', None):
            supplier_initial = self.instance.supplier
        self.fields['supplier'].initial = supplier_initial

    def clean(self):
        cleaned = super().clean()
        source_lot = cleaned.get('source_lot')
        product = cleaned.get('product')
        fsc_claim = (cleaned.get('fsc_claim') or '').strip()
        quantity = cleaned.get('quantity')
        movement_unit = cleaned.get('movement_unit')
        if source_lot and product and source_lot.product_id != product.id:
            self.add_error('source_lot', 'O lote selecionado pertence a outro produto.')
        if source_lot and fsc_claim and (source_lot.entry.fsc_claim if source_lot.entry_id else '') != fsc_claim:
            self.add_error('source_lot', 'O lote selecionado possui declaração FSC diferente da informada na saída.')
        if source_lot and quantity and movement_unit and product:
            try:
                qty_base = cleaned.get('quantity_base') or convert_to_base(product, quantity, movement_unit)
                available = get_lot_remaining_for_sale(source_lot, sale=self.instance if getattr(self.instance, 'pk', None) else None)
                if qty_base > available:
                    self.add_error('source_lot', f'Lote sem saldo suficiente. Disponível: {available} {product.get_unit_display()}.')
            except Exception as exc:
                self.add_error('source_lot', str(exc))
        cleaned['supplier'] = source_lot.supplier if source_lot else None
        return cleaned

class TransformationRecordForm(forms.ModelForm):
    source_unit = forms.ChoiceField(label='Unidade origem', choices=UNIT_CHOICES)
    new_source_product_name = forms.CharField(label='Novo produto origem (opcional)', required=False)
    new_target_product_name = forms.CharField(label='Novo produto destino (opcional)', required=False)

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
        new_source = (cleaned.get('new_source_product_name') or '').strip()
        new_target = (cleaned.get('new_target_product_name') or '').strip()

        if new_source and not source_product and source_unit:
            cleaned['new_source_product_payload'] = {'name': new_source, 'unit': source_unit}
        if new_target and not target_product:
            cleaned['new_target_product_payload'] = {'name': new_target}

        if source_product and source_quantity and source_unit and target_product:
            try:
                source_quantity_base = convert_to_base(source_product, source_quantity, source_unit)
                target_quantity_base = calculate_target_from_source(source_product, target_product, source_quantity_base)
                cleaned['source_quantity_base'] = source_quantity_base
                cleaned['target_quantity_base'] = target_quantity_base
            except Exception as exc:
                self.add_error(None, str(exc))
        return cleaned
