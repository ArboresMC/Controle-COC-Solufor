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
