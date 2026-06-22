from decimal import Decimal
from django.conf import settings
from django.db import models


UNIDADE_CHOICES = [
    ('m3', 'm³'),
    ('ton', 'Tonelada'),
    ('st', 'Estéreo (st)'),
]


class Especie(models.Model):
    """Espécie de árvore, cadastrada por participante, com fatores de conversão próprios."""
    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='especies',
    )
    nome = models.CharField('Nome da espécie', max_length=100)
    fator_m3_para_ton = models.DecimalField('Fator m³ → tonelada', max_digits=10, decimal_places=6)
    fator_m3_para_st = models.DecimalField('Fator m³ → st', max_digits=10, decimal_places=6)
    ativo = models.BooleanField('Ativa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('participant', 'nome')
        ordering = ['nome']
        verbose_name = 'Espécie'
        verbose_name_plural = 'Espécies'

    def __str__(self):
        return self.nome

    def converter_para_m3(self, volume, unidade):
        """Converte um volume informado em qualquer unidade para m³."""
        volume = Decimal(str(volume))
        if unidade == 'm3':
            return volume
        if unidade == 'ton':
            return volume / self.fator_m3_para_ton
        if unidade == 'st':
            return volume / self.fator_m3_para_st
        raise ValueError(f'Unidade desconhecida: {unidade}')

    def converter_de_m3(self, volume_m3, unidade):
        """Converte um volume em m³ para a unidade desejada (uso em relatórios)."""
        volume_m3 = Decimal(str(volume_m3))
        if unidade == 'm3':
            return volume_m3
        if unidade == 'ton':
            return volume_m3 * self.fator_m3_para_ton
        if unidade == 'st':
            return volume_m3 * self.fator_m3_para_st
        raise ValueError(f'Unidade desconhecida: {unidade}')


class Propriedade(models.Model):
    """Propriedade/projeto certificado em Manejo Florestal."""
    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='propriedades',
    )
    nome = models.CharField('Nome do projeto/propriedade', max_length=255)
    codigo = models.CharField('Código/CAR', max_length=100, blank=True)
    municipio = models.CharField('Município', max_length=120, blank=True)
    uf = models.CharField('UF', max_length=2, blank=True)
    area_hectares = models.DecimalField('Área (ha)', max_digits=12, decimal_places=2, null=True, blank=True)
    ativa = models.BooleanField('Ativa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('participant', 'nome')
        ordering = ['nome']
        verbose_name = 'Propriedade'
        verbose_name_plural = 'Propriedades'

    def __str__(self):
        return self.nome


class InventarioEntrada(models.Model):
    """Entrada de inventário: volume certificado de uma propriedade+espécie específica."""
    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='inventarios',
    )
    propriedade = models.ForeignKey(Propriedade, on_delete=models.PROTECT, related_name='entradas')
    especie = models.ForeignKey(Especie, on_delete=models.PROTECT, related_name='entradas')
    data = models.DateField('Data do inventário')
    documento = models.CharField('Documento/Contrato', max_length=100, blank=True)
    volume = models.DecimalField('Volume informado', max_digits=14, decimal_places=4)
    unidade = models.CharField('Unidade', max_length=10, choices=UNIDADE_CHOICES, default='m3')
    volume_m3 = models.DecimalField('Volume padronizado (m³)', max_digits=14, decimal_places=4)
    observacoes = models.TextField('Observações', blank=True)
    attachment = models.FileField('Anexo', upload_to='manejo/inventarios/', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data', '-id']
        verbose_name = 'Entrada de Inventário'
        verbose_name_plural = 'Entradas de Inventário'

    def __str__(self):
        return f"{self.propriedade} — {self.especie} ({self.volume_m3} m³)"

    @property
    def volume_vendido_m3(self):
        from django.db.models import Sum
        total = self.saidas.aggregate(total=Sum('volume_m3'))['total']
        return total or Decimal('0')

    @property
    def saldo_disponivel_m3(self):
        return self.volume_m3 - self.volume_vendido_m3


class SaidaManejo(models.Model):
    """Saída/venda de madeira a partir de uma entrada de inventário (propriedade+espécie)."""
    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='saidas_manejo',
    )
    entrada = models.ForeignKey(InventarioEntrada, on_delete=models.PROTECT, related_name='saidas')
    data = models.DateField('Data')
    documento = models.CharField('Nº NF', max_length=100, blank=True)
    cliente_nome = models.CharField('Cliente', max_length=255, blank=True)
    declaracao_fsc = models.BooleanField('Declaração FSC', default=True)
    volume = models.DecimalField('Volume informado', max_digits=14, decimal_places=4)
    unidade = models.CharField('Unidade', max_length=10, choices=UNIDADE_CHOICES, default='m3')
    volume_m3 = models.DecimalField('Volume padronizado (m³)', max_digits=14, decimal_places=4)
    observacoes = models.TextField('Observações', blank=True)
    attachment = models.FileField('Anexo', upload_to='manejo/saidas/', null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data', '-id']
        verbose_name = 'Saída de Manejo'
        verbose_name_plural = 'Saídas de Manejo'

    def __str__(self):
        return f"{self.entrada.propriedade} — {self.volume_m3} m³ ({self.data})"
