from django.db import models


class Organization(models.Model):
    name = models.CharField('Nome do ambiente', max_length=255, unique=True)
    legal_name = models.CharField('Razão social do ambiente', max_length=255, blank=True)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ambiente'
        verbose_name_plural = 'Ambientes'

    def __str__(self):
        return self.name


class Participant(models.Model):
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('suspended', 'Suspenso'),
    ]
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='participants',
        verbose_name='Ambiente',
    )
    legal_name = models.CharField('Razão social', max_length=255)
    trade_name = models.CharField('Nome fantasia', max_length=255, blank=True)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True)
    contact_name = models.CharField('Responsável', max_length=255, blank=True)
    contact_email = models.EmailField('E-mail', blank=True)
    contact_phone = models.CharField('Telefone', max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['trade_name', 'legal_name']
        indexes = [
            models.Index(fields=['organization', 'status'], name='part_org_status_idx'),
            models.Index(fields=['organization', 'trade_name'], name='part_org_trade_idx'),
        ]

    def __str__(self):
        return self.trade_name or self.legal_name
