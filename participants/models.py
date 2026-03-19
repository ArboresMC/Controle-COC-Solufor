from django.db import models

class Participant(models.Model):
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('suspended', 'Suspenso'),
    ]
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

    def __str__(self):
        return self.trade_name or self.legal_name
