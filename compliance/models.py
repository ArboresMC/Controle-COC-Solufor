from django.conf import settings
from django.db import models

class MonthlyClosing(models.Model):
    STATUS_CHOICES = [
        ('open', 'Aberto'),
        ('submitted', 'Enviado'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('overdue', 'Em atraso'),
    ]
    participant = models.ForeignKey('participants.Participant', on_delete=models.CASCADE)
    year = models.PositiveIntegerField('Ano')
    month = models.PositiveSmallIntegerField('Mês')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    submitted_at = models.DateTimeField('Enviado em', blank=True, null=True)
    reviewed_at = models.DateTimeField('Revisado em', blank=True, null=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_closings')
    manager_notes = models.TextField('Observações do gestor', blank=True)
    participant_notes = models.TextField('Observações do participante', blank=True)
    declaration_no_movement = models.BooleanField('Sem movimentação', default=False)

    class Meta:
        unique_together = ('participant', 'year', 'month')
        ordering = ['-year', '-month', 'participant__trade_name']

    def __str__(self):
        return f'{self.participant} - {self.month:02d}/{self.year}'
