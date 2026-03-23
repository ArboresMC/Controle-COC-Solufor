from django import forms
from catalog.models import Counterparty, Product, FSCClaim
from .models import EntryRecord, SaleRecord, TransformationRecord, TraceLot
from .services import (
    calculate_target_from_source,
    convert_to_base,
    get_lot_remaining_for_sale,
    get_lot_remaining_for_transformation,
    get_manual_sale_lot_choices,
    get_manual_transformation_lot_choices,
    get_transformation_rule,
    to_decimal,
)


class DateInput(forms.DateInput):
    input_type = 'date'


UNIT_CHOICES = Product.UNIT_CHOICES


class BaseMovementForm(forms.ModelForm):
    movement_unit = forms.ChoiceField(label='Unidade', choices=UNIT_CHOICES)
    new_product_name = forms.CharField(label='Novo produto (opcional)', required=False)
    fsc_claim = forms.ModelChoiceField(
        label='Declaração FSC',
        queryset=FSCClaim.objects.filter(active=True).order_by('sort_order', 'name'),
        required=False,
        empty_label='Selecione',
    )

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
        self.fields['fsc_claim'].queryset = FSCClaim.objects.filter(active=True).order_by('sort_order', 'name')
        if self.instance and getattr(self.instance, 'pk', None) and self.instance.movement_unit:
            self.fields['movement_unit'].initial = self.instance.movement_unit
        elif self.instance and getattr(self.instance, 'pk', None) and self.instance.product_id:
            self.fields['movement_unit'].initial = self.instance.product.unit
        if self.instance and getattr(self.instance, 'pk', None) and getattr(self.instance, 'fsc_claim', ''):
            self.fields['fsc_claim'].initial = FSCClaim.objects.filter(name=self.instance.fsc_claim).first()
        self.fields['new_product_name'].help_text = 'Se informado, cria o produto usando a unidade selecionada como unidade base.'

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get('product')
        quantity = cleaned.get('quantity')
        movement_unit = cleaned.get('movement_unit')
        new_product_name = (cleaned.get('new_product_name') or '').strip()
        fsc_claim = cleaned.get('fsc_claim')
        if fsc_claim is not None:
            cleaned['fsc_claim_name'] = fsc_claim.name
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
        self.fields['fsc_claim'].disabled = True
        self.fields['fsc_claim'].help_text = 'A declaração FSC é herdada automaticamente do lote de origem.'

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
            source_lot_id = self.data.get('source_lot')
            if source_lot_id:
                try:
                    selected_claim = TraceLot.objects.get(pk=source_lot_id).fsc_claim or None
                except TraceLot.DoesNotExist:
                    selected_claim = None
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
        claim_initial = None
        if self.is_bound:
            source_lot_id = self.data.get('source_lot')
            if source_lot_id:
                try:
                    source_lot = TraceLot.objects.select_related('supplier').get(pk=source_lot_id)
                    supplier_initial = source_lot.supplier
                    claim_initial = FSCClaim.objects.filter(name=source_lot.fsc_claim).first() if source_lot.fsc_claim else None
                except TraceLot.DoesNotExist:
                    supplier_initial = None
        else:
            if self.instance and getattr(self.instance, 'supplier_id', None):
                supplier_initial = self.instance.supplier
            if self.instance and getattr(self.instance, 'fsc_claim', ''):
                claim_initial = FSCClaim.objects.filter(name=self.instance.fsc_claim).first()
        self.fields['supplier'].initial = supplier_initial
        self.fields['fsc_claim'].initial = claim_initial

    def clean(self):
        cleaned = super().clean()
        source_lot = cleaned.get('source_lot')
        product = cleaned.get('product')
        quantity = cleaned.get('quantity')
        movement_unit = cleaned.get('movement_unit')
        if source_lot and product and source_lot.product_id != product.id:
            self.add_error('source_lot', 'O lote selecionado pertence a outro produto.')
        if source_lot and quantity and movement_unit and product:
            try:
                qty_base = cleaned.get('quantity_base') or convert_to_base(product, quantity, movement_unit)
                available = get_lot_remaining_for_sale(source_lot, sale=self.instance if getattr(self.instance, 'pk', None) else None)
                if qty_base > available:
                    self.add_error('source_lot', f'Lote sem saldo suficiente. Disponível: {available} {product.get_unit_display()}.')
            except Exception as exc:
                self.add_error('source_lot', str(exc))
        cleaned['supplier'] = source_lot.supplier if source_lot else None
        cleaned['fsc_claim_name'] = source_lot.fsc_claim if source_lot else ''
        return cleaned


class TransformationRecordForm(forms.ModelForm):
    source_lot = forms.ModelChoiceField(
        label='Entrada/lote de tora',
        queryset=TraceLot.objects.none(),
        required=True,
        empty_label='Selecione o lote de origem',
    )
    target_quantity = forms.DecimalField(label='Quantidade produzida', min_value=0.001)
    new_target_product_name = forms.CharField(label='Novo produto destino (opcional)', required=False)
    new_customer_name = forms.CharField(label='Novo cliente final (opcional)', required=False)
    supplier = forms.ModelChoiceField(
        label='Fornecedor de origem',
        queryset=Counterparty.objects.none(),
        required=False,
        disabled=True,
    )
    fsc_claim = forms.ModelChoiceField(
        label='Declaração FSC',
        queryset=FSCClaim.objects.filter(active=True).order_by('sort_order', 'name'),
        required=False,
        disabled=True,
        empty_label='Será herdada da origem',
    )

    class Meta:
        model = TransformationRecord
        fields = [
            'movement_date',
            'document_number',
            'customer',
            'supplier',
            'fsc_claim',
            'source_lot',
            'target_product',
            'target_quantity',
            'notes',
            'attachment',
        ]
        widgets = {'movement_date': DateInput()}

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        self.participant = participant

        self.fields['target_product'].queryset = Product.objects.filter(active=True).order_by('name')
        customer_qs = Counterparty.objects.filter(type__in=['customer', 'both'])
        supplier_qs = Counterparty.objects.filter(type__in=['supplier', 'both'])
        if participant:
            customer_qs = customer_qs.filter(participant__in=[participant, None])
            supplier_qs = supplier_qs.filter(participant__in=[participant, None])
        self.fields['customer'].queryset = customer_qs.order_by('name')
        self.fields['supplier'].queryset = supplier_qs.order_by('name')

        self.fields['new_customer_name'].help_text = 'Se informado, cria um novo cliente final para este participante.'
        self.fields['target_quantity'].help_text = 'Informe a quantidade produzida no produto destino. O sistema calculará automaticamente o consumo da tora pela regra de rendimento.'
        self.fields['source_lot'].help_text = 'Selecione a entrada/lote de tora que será consumido na transformação. O sistema herdará fornecedor e declaração FSC desse lote.'
        self.fields['supplier'].help_text = 'O fornecedor é herdado automaticamente do lote de origem.'
        self.fields['fsc_claim'].help_text = 'A declaração FSC é herdada automaticamente do lote de origem.'
        self.fields['target_product'].help_text = 'Selecione o produto final gerado. O rendimento cadastrado definirá o consumo da origem.'

        selected_lot = None
        if self.is_bound:
            source_lot_id = self.data.get('source_lot')
            if source_lot_id:
                try:
                    selected_lot = TraceLot.objects.select_related('supplier', 'product').get(pk=source_lot_id)
                except TraceLot.DoesNotExist:
                    selected_lot = None
        elif self.instance and getattr(self.instance, 'pk', None):
            existing_allocation = self.instance.source_lot_allocations.select_related('lot', 'lot__supplier', 'lot__product').first()
            selected_lot = existing_allocation.lot if existing_allocation else None
            if self.instance.target_quantity_base is not None:
                self.fields['target_quantity'].initial = to_decimal(self.instance.target_quantity_base)
            self.fields['supplier'].initial = self.instance.supplier
            if self.instance.fsc_claim:
                self.fields['fsc_claim'].initial = FSCClaim.objects.filter(name=self.instance.fsc_claim).first()

        if participant:
            lot_choices = get_manual_transformation_lot_choices(
                participant,
                transformation=self.instance if getattr(self.instance, 'pk', None) else None,
                product=selected_lot.product if selected_lot else None,
            )
            lot_ids = [item['lot'].id for item in lot_choices]
            self.fields['source_lot'].queryset = TraceLot.objects.filter(pk__in=lot_ids).select_related('product', 'supplier', 'entry', 'transformation').order_by('movement_date', 'id')
            self.available_lot_choices = lot_choices
        else:
            self.available_lot_choices = []

        if selected_lot:
            self.fields['source_lot'].initial = selected_lot
            self.fields['supplier'].initial = selected_lot.supplier
            if selected_lot.fsc_claim:
                self.fields['fsc_claim'].initial = FSCClaim.objects.filter(name=selected_lot.fsc_claim).first()

    def clean(self):
        cleaned = super().clean()
        source_lot = cleaned.get('source_lot')
        target_product = cleaned.get('target_product')
        target_quantity = cleaned.get('target_quantity')
        new_target = (cleaned.get('new_target_product_name') or '').strip()

        if new_target and not target_product:
            cleaned['new_target_product_payload'] = {'name': new_target}

        if source_lot:
            cleaned['source_product'] = source_lot.product
            cleaned['source_unit'] = source_lot.product.unit
            cleaned['supplier'] = source_lot.supplier
            cleaned['fsc_claim_name'] = source_lot.fsc_claim or ''
        else:
            cleaned['fsc_claim_name'] = ''

        if source_lot and target_product and target_quantity:
            try:
                rule = get_transformation_rule(
                    source_lot.product,
                    target_product,
                    participant=self.participant,
                )
                if not rule:
                    raise ValueError('Não existe regra de transformação cadastrada para os produtos selecionados para esta empresa.')

                target_quantity_base = convert_to_base(
                    target_product,
                    target_quantity,
                    target_product.unit,
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
                    f'Lote sem saldo suficiente. Disponível: {available} {source_lot.product.get_unit_display()}. Necessário para a produção informada: {source_quantity_base} {source_lot.product.get_unit_display()}.'
                )

        return cleaned

    def _post_clean(self):
        self.instance.source_product = self.cleaned_data.get('source_product')
        self.instance.source_quantity = self.cleaned_data.get('source_quantity_base')
        self.instance.source_unit = self.cleaned_data.get('source_unit')
        self.instance.target_product = self.cleaned_data.get('target_product')
        super()._post_clean()
