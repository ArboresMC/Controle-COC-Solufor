
from django import forms
from catalog.models import Counterparty, Product, FSCClaim
from .models import EntryRecord, SaleRecord, TransformationRecord, TraceLot
from .services import calculate_target_from_source, convert_to_base, convert_from_base, get_lot_remaining_for_sale, get_manual_sale_lot_choices, get_transformation_rule


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
    source_unit = forms.ChoiceField(label='Unidade de consumo da origem', choices=UNIT_CHOICES)
    target_quantity = forms.DecimalField(label='Quantidade destino informada', max_digits=14, decimal_places=3)
    target_unit = forms.ChoiceField(label='Unidade destino', choices=UNIT_CHOICES)
    estimated_source_quantity = forms.DecimalField(label='Consumo estimado da origem', max_digits=14, decimal_places=3, required=False, disabled=True)
    new_source_product_name = forms.CharField(label='Novo produto origem (opcional)', required=False)
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
            'source_product',
            'source_unit',
            'target_product',
            'target_quantity',
            'target_unit',
            'estimated_source_quantity',
            'notes',
            'attachment',
        ]
        widgets = {'movement_date': DateInput()}

    def __init__(self, *args, **kwargs):
        participant = kwargs.pop('participant', None)
        super().__init__(*args, **kwargs)
        self.fields['source_product'].queryset = Product.objects.filter(active=True).order_by('name')
        self.fields['target_product'].queryset = Product.objects.filter(active=True).order_by('name')
        customer_qs = Counterparty.objects.filter(type__in=['customer', 'both'])
        supplier_qs = Counterparty.objects.filter(type__in=['supplier', 'both'])
        if participant:
            customer_qs = customer_qs.filter(participant__in=[participant, None])
            supplier_qs = supplier_qs.filter(participant__in=[participant, None])
        self.fields['customer'].queryset = customer_qs.order_by('name')
        self.fields['supplier'].queryset = supplier_qs.order_by('name')
        self.fields['new_customer_name'].help_text = 'Se informado, cria um novo cliente final para este participante.'
        self.fields['supplier'].help_text = 'O fornecedor é herdado automaticamente dos lotes consumidos.'
        self.fields['fsc_claim'].help_text = 'A declaração FSC é herdada automaticamente dos lotes consumidos.'
        self.fields['target_quantity'].help_text = 'Informe aqui o volume/quantidade efetiva gerada ou vendida do produto destino. O consumo da origem será calculado automaticamente.'
        self.fields['estimated_source_quantity'].help_text = 'Valor calculado automaticamente a partir do fator de rendimento da empresa.'
        if self.instance and getattr(self.instance, 'pk', None):
            self.fields['source_unit'].initial = self.instance.source_unit
            self.fields['target_unit'].initial = self.instance.target_unit_snapshot
            self.fields['target_quantity'].initial = self.instance.target_quantity_base
            self.fields['estimated_source_quantity'].initial = self.instance.source_quantity
            self.fields['supplier'].initial = self.instance.supplier
            if self.instance.fsc_claim:
                self.fields['fsc_claim'].initial = FSCClaim.objects.filter(name=self.instance.fsc_claim).first()
        self.participant = participant

    def clean(self):
        cleaned = super().clean()
        source_product = cleaned.get('source_product')
        source_unit = cleaned.get('source_unit')
        target_product = cleaned.get('target_product')
        target_quantity = cleaned.get('target_quantity')
        target_unit = cleaned.get('target_unit')
        new_source = (cleaned.get('new_source_product_name') or '').strip()
        new_target = (cleaned.get('new_target_product_name') or '').strip()

        if new_source and not source_product and source_unit:
            cleaned['new_source_product_payload'] = {'name': new_source, 'unit': source_unit}
        if new_target and not target_product:
            cleaned['new_target_product_payload'] = {'name': new_target}

        if source_product and target_product and target_quantity and target_unit and source_unit:
            try:
                target_quantity_base = convert_to_base(target_product, target_quantity, target_unit)
                rule = get_transformation_rule(source_product, target_product, participant=self.participant)
                if not rule:
                    raise ValueError('Não existe regra de transformação cadastrada para os produtos selecionados para esta empresa.')
                if rule.yield_factor <= 0:
                    raise ValueError('O fator de rendimento da regra precisa ser maior que zero.')
                source_quantity_base = (target_quantity_base / rule.yield_factor).quantize(target_quantity_base)
                estimated_source_quantity = convert_from_base(source_product, source_quantity_base, source_unit)
                cleaned['source_quantity_base'] = source_quantity_base
                cleaned['target_quantity_base'] = target_quantity_base
                cleaned['estimated_source_quantity'] = estimated_source_quantity
                self.fields['estimated_source_quantity'].initial = estimated_source_quantity
            except Exception as exc:
                self.add_error(None, str(exc))
        return cleaned
