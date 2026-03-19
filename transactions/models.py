from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class BaseMovement(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('submitted', 'Enviado'),
        ('reviewed', 'Revisado'),
        ('needs_correction', 'Precisa correção'),
    ]
    participant = models.ForeignKey('participants.Participant', on_delete=models.CASCADE)
    movement_date = models.DateField('Data da movimentação')
    document_number = models.CharField('Número do documento', max_length=50)
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT)
    quantity = models.DecimalField('Quantidade informada', max_digits=14, decimal_places=3)
    movement_unit = models.CharField('Unidade informada', max_length=10, choices=[('m3', 'm³'), ('kg', 'kg'), ('t', 't'), ('un', 'un')], blank=True)
    unit_snapshot = models.CharField('Unidade base', max_length=10, choices=[('m3', 'm³'), ('kg', 'kg'), ('t', 't'), ('un', 'un')])
    quantity_base = models.DecimalField('Quantidade convertida (unidade base)', max_digits=14, decimal_places=3, default=0)
    fsc_claim = models.CharField('Declaração FSC', max_length=100, blank=True)
    batch_code = models.CharField('Lote', max_length=100, blank=True)
    notes = models.TextField('Observações', blank=True)
    attachment = models.FileField(upload_to='attachments/%Y/%m/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    class Meta:
        abstract = True
        ordering = ['-movement_date', '-id']

    def clean(self):
        if self.movement_date > timezone.localdate():
            raise ValidationError('A data da movimentação não pode estar no futuro.')
        if self.quantity <= 0:
            raise ValidationError('A quantidade deve ser maior que zero.')
        if self.product and not self.product.active:
            raise ValidationError('O produto selecionado está inativo.')
        if self.product and not self.movement_unit:
            self.movement_unit = self.product.unit
        if self.product:
            self.unit_snapshot = self.product.unit


class EntryRecord(BaseMovement):
    supplier = models.ForeignKey('catalog.Counterparty', on_delete=models.PROTECT, related_name='entries')

    def __str__(self):
        return f'Entrada {self.document_number}'


class SaleRecord(BaseMovement):
    customer = models.ForeignKey('catalog.Counterparty', on_delete=models.PROTECT, related_name='sales')
    supplier = models.ForeignKey(
        'catalog.Counterparty',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='sales_as_source_supplier',
        verbose_name='Fornecedor de origem',
    )

    def __str__(self):
        return f'Saída {self.document_number}'


class TransformationRecord(models.Model):
    participant = models.ForeignKey('participants.Participant', on_delete=models.CASCADE)
    movement_date = models.DateField('Data da transformação')
    source_product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT, related_name='transformations_as_source')
    source_quantity = models.DecimalField('Quantidade origem', max_digits=14, decimal_places=3)
    source_unit = models.CharField('Unidade origem informada', max_length=10, choices=[('m3', 'm³'), ('kg', 'kg'), ('t', 't'), ('un', 'un')])
    source_quantity_base = models.DecimalField('Quantidade origem convertida', max_digits=14, decimal_places=3, default=0)
    target_product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT, related_name='transformations_as_target')
    target_quantity_base = models.DecimalField('Quantidade destino gerada', max_digits=14, decimal_places=3, default=0)
    target_unit_snapshot = models.CharField('Unidade base destino', max_length=10, choices=[('m3', 'm³'), ('kg', 'kg'), ('t', 't'), ('un', 'un')])
    yield_factor_snapshot = models.DecimalField('Fator de rendimento aplicado', max_digits=14, decimal_places=6, default=0)
    notes = models.TextField('Observações', blank=True)
    attachment = models.FileField(upload_to='transformations/%Y/%m/', blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-movement_date', '-id']
        verbose_name = 'Transformação'
        verbose_name_plural = 'Transformações'

    def clean(self):
        if self.movement_date > timezone.localdate():
            raise ValidationError('A data da transformação não pode estar no futuro.')
        if self.source_quantity <= 0:
            raise ValidationError('A quantidade de origem deve ser maior que zero.')
        if self.source_product_id and self.target_product_id and self.source_product_id == self.target_product_id:
            raise ValidationError('Produto de origem e produto de destino não podem ser iguais.')

    def __str__(self):
        return f'Transformação {self.source_product} → {self.target_product}'


class TraceLot(models.Model):
    SOURCE_CHOICES = [
        ('entry', 'Entrada'),
        ('transformation', 'Transformação'),
    ]
    participant = models.ForeignKey('participants.Participant', on_delete=models.CASCADE, related_name='trace_lots')
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT, related_name='trace_lots')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    entry = models.OneToOneField(EntryRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='trace_lot')
    transformation = models.OneToOneField(TransformationRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='target_trace_lot')
    supplier = models.ForeignKey('catalog.Counterparty', on_delete=models.PROTECT, null=True, blank=True, related_name='trace_lots')
    fsc_claim = models.CharField('Declaração FSC', max_length=100, blank=True)
    movement_date = models.DateField('Data de origem')
    quantity_base = models.DecimalField('Quantidade do lote', max_digits=14, decimal_places=3, default=0)
    unit_snapshot = models.CharField('Unidade base', max_length=10, choices=[('m3', 'm³'), ('kg', 'kg'), ('t', 't'), ('un', 'un')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['movement_date', 'id']
        verbose_name = 'Lote rastreável'
        verbose_name_plural = 'Lotes rastreáveis'

    def clean(self):
        if self.source_type == 'entry' and not self.entry_id:
            raise ValidationError('Lotes de entrada precisam estar vinculados a uma entrada.')
        if self.source_type == 'transformation' and not self.transformation_id:
            raise ValidationError('Lotes de transformação precisam estar vinculados a uma transformação.')

    def __str__(self):
        return self.label

    @property
    def label(self):
        if self.source_type == 'entry' and self.entry_id:
            supplier = f' · {self.supplier}' if self.supplier_id else ''
            return f'Entrada {self.entry.document_number}{supplier}'
        if self.source_type == 'transformation' and self.transformation_id:
            return f'Transformação #{self.transformation_id} → {self.product}'
        return f'Lote #{self.pk}'


class LotAllocation(models.Model):
    TARGET_CHOICES = [
        ('sale', 'Saída'),
        ('transformation', 'Transformação'),
    ]
    participant = models.ForeignKey('participants.Participant', on_delete=models.CASCADE, related_name='lot_allocations')
    lot = models.ForeignKey(TraceLot, on_delete=models.CASCADE, related_name='allocations')
    sale = models.ForeignKey(SaleRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='lot_allocations')
    transformation = models.ForeignKey(TransformationRecord, on_delete=models.CASCADE, null=True, blank=True, related_name='source_lot_allocations')
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    quantity_base = models.DecimalField('Quantidade alocada', max_digits=14, decimal_places=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        verbose_name = 'Alocação de lote'
        verbose_name_plural = 'Alocações de lotes'

    def clean(self):
        if self.target_type == 'sale' and not self.sale_id:
            raise ValidationError('Alocações de saída precisam de uma saída vinculada.')
        if self.target_type == 'transformation' and not self.transformation_id:
            raise ValidationError('Alocações de transformação precisam de uma transformação vinculada.')

    def __str__(self):
        target = self.sale or self.transformation
        return f'{self.lot} → {target} ({self.quantity_base})'
