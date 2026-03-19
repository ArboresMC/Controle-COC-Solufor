from django.db import models


class FSCClaim(models.Model):
    name = models.CharField('Declaração FSC', max_length=100, unique=True)
    code = models.SlugField('Código', max_length=50, unique=True)
    active = models.BooleanField('Ativo', default=True)
    sort_order = models.PositiveIntegerField('Ordem', default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = 'Declaração FSC'
        verbose_name_plural = 'Declarações FSC'

    def __str__(self):
        return self.name


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


class ProductUnitConversion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='unit_conversions')
    from_unit = models.CharField('Unidade de origem', max_length=10, choices=Product.UNIT_CHOICES)
    to_unit = models.CharField('Unidade de destino', max_length=10, choices=Product.UNIT_CHOICES)
    factor = models.DecimalField('Fator de conversão', max_digits=14, decimal_places=6, help_text='Multiplica a quantidade da unidade de origem para chegar na unidade de destino.')
    notes = models.CharField('Observações', max_length=255, blank=True)
    active = models.BooleanField('Ativo', default=True)

    class Meta:
        ordering = ['product__name', 'from_unit', 'to_unit']
        verbose_name = 'Conversão de unidade'
        verbose_name_plural = 'Conversões de unidade'
        unique_together = ('product', 'from_unit', 'to_unit')

    def __str__(self):
        return f'{self.product}: {self.from_unit} → {self.to_unit} ({self.factor})'


class ProductTransformationRule(models.Model):
    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='transformation_rules',
        verbose_name='Participante',
        null=True,
        blank=True,
        help_text='Deixe em branco para usar como regra geral. Regras específicas do participante têm prioridade.',
    )
    source_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transformation_rules_out')
    target_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transformation_rules_in')
    yield_factor = models.DecimalField('Fator de rendimento', max_digits=14, decimal_places=6, help_text='Quantidade do produto destino gerada a partir de 1 unidade base do produto origem.')
    notes = models.CharField('Observações', max_length=255, blank=True)
    active = models.BooleanField('Ativo', default=True)

    class Meta:
        ordering = ['participant__trade_name', 'participant__legal_name', 'source_product__name', 'target_product__name']
        verbose_name = 'Regra de transformação'
        verbose_name_plural = 'Regras de transformação'
        unique_together = ('participant', 'source_product', 'target_product')

    def __str__(self):
        owner = self.participant or 'Regra geral'
        return f'{owner} | {self.source_product} → {self.target_product} ({self.yield_factor})'
