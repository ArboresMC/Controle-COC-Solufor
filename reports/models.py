from django.conf import settings
from django.db import models
from django.utils import timezone


def import_workbook_path(instance, filename):
    org_slug = getattr(getattr(instance.participant, 'organization', None), 'slug', None) or 'sem-organizacao'
    stamp = timezone.localtime().strftime('%Y/%m')
    safe_name = ''.join(ch if ch.isalnum() or ch in ('-', '_', '.') else '-' for ch in filename).strip('-') or 'planilha.xlsx'
    return f"imports/{org_slug}/{stamp}/{safe_name}"


class ImportJob(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_PROCESSING, 'Processando'),
        (STATUS_COMPLETED, 'Concluído'),
        (STATUS_FAILED, 'Falhou'),
    ]

    participant = models.ForeignKey('participants.Participant', on_delete=models.CASCADE, related_name='import_jobs')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_import_jobs')
    workbook = models.FileField(upload_to=import_workbook_path)
    original_filename = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    summary = models.JSONField(default=dict, blank=True)
    error_messages = models.JSONField(default=list, blank=True)
    preview = models.JSONField(default=dict, blank=True)
    progress_current = models.PositiveIntegerField(default=0)
    progress_total = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['participant', 'created_at']),
            models.Index(fields=['created_by', 'created_at']),
        ]
        verbose_name = 'Job de importação'
        verbose_name_plural = 'Jobs de importação'

    def __str__(self):
        return f'Importação #{self.pk} - {self.get_status_display()}'
