from django.db import models

class Product(models.Model):
    UNIT_CHOICES = [
        ('m3', 'm³'),
        ('kg', 'kg'),
        ('t', 't'),
        ('un', 'un'),
    ]
    name = models.CharField('Produto', max_length=255)
    category = models.CharField('Categoria', max_length=100, blank=True)
    unit = models.CharField('Unidade', max_length=10, choices=UNIT_CHOICES)
    fsc_applicable = models.BooleanField('Aplica FSC', default=True)
    default_claim = models.CharField('Declaração padrão', max_length=100, blank=True)
    active = models.BooleanField('Ativo', default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Counterparty(models.Model):
    TYPE_CHOICES = [
        ('supplier', 'Fornecedor'),
        ('customer', 'Cliente'),
        ('both', 'Ambos'),
    ]
    participant = models.ForeignKey(
        'participants.Participant', on_delete=models.CASCADE,
        null=True, blank=True, related_name='counterparties'
    )
    name = models.CharField('Nome', max_length=255)
    document_id = models.CharField('Documento', max_length=30, blank=True)
    type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES, default='both')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
