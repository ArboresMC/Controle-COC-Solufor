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
    quantity = models.DecimalField('Quantidade', max_digits=14, decimal_places=3)
    unit_snapshot = models.CharField('Unidade', max_length=10)
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

class EntryRecord(BaseMovement):
    supplier = models.ForeignKey('catalog.Counterparty', on_delete=models.PROTECT, related_name='entries')

    def __str__(self):
        return f'Entrada {self.document_number}'

class SaleRecord(BaseMovement):
    customer = models.ForeignKey('catalog.Counterparty', on_delete=models.PROTECT, related_name='sales')

    def __str__(self):
        return f'Saída {self.document_number}'
