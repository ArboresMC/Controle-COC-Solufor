from django.db import models
from django.conf import settings


class MonthlyClosing(models.Model):
    STATUS_OPEN = 'open'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Aberto'),
        (STATUS_SUBMITTED, 'Aguardando aprovação'),
        (STATUS_APPROVED, 'Aprovado'),
        (STATUS_REJECTED, 'Rejeitado'),
    ]

    participant = models.ForeignKey(
        'participants.Participant',
        on_delete=models.CASCADE,
        related_name='monthly_closings',
    )
    year = models.PositiveIntegerField(verbose_name='Ano')
    month = models.PositiveIntegerField(verbose_name='Mês')

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )

    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Enviado em')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Revisado em')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_closings',
        verbose_name='Revisado por',
    )
    rejection_reason = models.TextField(blank=True, null=True, verbose_name='Motivo da rejeição')

    # Campos herdados do modelo original — mantidos para compatibilidade com o banco
    manager_notes = models.TextField(blank=True, default='', verbose_name='Observações do gestor')
    participant_notes = models.TextField(blank=True, default='', verbose_name='Observações do participante')
    declaration_no_movement = models.BooleanField(default=False, verbose_name='Sem movimentação')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('participant', 'year', 'month')
        ordering = ['-year', '-month']
        verbose_name = 'Fechamento Mensal'
        verbose_name_plural = 'Fechamentos Mensais'

    def __str__(self):
        return f"{self.participant} — {self.month:02d}/{self.year} [{self.get_status_display()}]"

    @property
    def period_display(self):
        meses_pt = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return f"{meses_pt[self.month - 1]}/{self.year}"

    @property
    def is_editable(self):
        return self.status in (self.STATUS_OPEN, self.STATUS_REJECTED)

    @property
    def is_locked(self):
        return self.status == self.STATUS_APPROVED


class BillingTier(models.Model):
    """Faixa de cobrança configurável pelo gestor.

    Os limites de cada faixa são fixos no código (definidos em
    transactions.views.BillingReportView), apenas o valor em R$ de
    cada faixa é editável e fica persistido aqui.
    """
    MODULO_COC = 'coc'
    MODULO_FM = 'fm'
    MODULO_CHOICES = [
        (MODULO_COC, 'Cadeia de Custódia'),
        (MODULO_FM, 'Manejo Florestal'),
    ]

    modulo = models.CharField(max_length=10, choices=MODULO_CHOICES, verbose_name='Módulo')
    ordem = models.PositiveIntegerField(verbose_name='Ordem da faixa')
    limite_max = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Limite máximo da faixa',
        help_text='Vazio significa "acima do limite anterior" (última faixa).',
    )
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor mensal (R$)')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('modulo', 'ordem')
        ordering = ['modulo', 'ordem']
        verbose_name = 'Faixa de Cobrança'
        verbose_name_plural = 'Faixas de Cobrança'

    def __str__(self):
        teto = f"até {self.limite_max}" if self.limite_max else "acima"
        return f"{self.get_modulo_display()} — {teto}: R$ {self.valor}"
