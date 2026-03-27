import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from reports.models import ImportJob
from reports.services import process_import_job


class Command(BaseCommand):
    help = 'Processa jobs de importação em fila usando o próprio banco de dados, sem custo adicional.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true', help='Processa apenas um ciclo e encerra.')
        parser.add_argument('--sleep', type=float, default=3, help='Intervalo entre verificações da fila.')
        parser.add_argument('--stale-minutes', type=int, default=30, help='Recoloca jobs travados após esse tempo.')

    def handle(self, *args, **options):
        once = options['once']
        sleep_seconds = options['sleep']
        stale_minutes = options['stale_minutes']

        self.stdout.write(self.style.SUCCESS('Worker de importação iniciado.'))

        while True:
            reclaimed = ImportJob.objects.filter(
                status=ImportJob.STATUS_PROCESSING,
                last_heartbeat__lt=timezone.now() - timedelta(minutes=stale_minutes),
            ).update(status=ImportJob.STATUS_PENDING)
            if reclaimed:
                self.stdout.write(self.style.WARNING(f'{reclaimed} job(s) travado(s) recolocados na fila.'))

            job = None
            with transaction.atomic():
                job = (
                    ImportJob.objects
                    .select_for_update(skip_locked=True)
                    .select_related('participant', 'created_by')
                    .filter(status=ImportJob.STATUS_PENDING)
                    .order_by('created_at', 'id')
                    .first()
                )
                if job:
                    job.status = ImportJob.STATUS_PROCESSING
                    job.started_at = timezone.now()
                    job.last_heartbeat = timezone.now()
                    job.save(update_fields=['status', 'started_at', 'last_heartbeat', 'updated_at'])

            if job:
                self.stdout.write(f'Processando job #{job.pk} ({job.original_filename or "sem nome"})')
                try:
                    process_import_job(job)
                    self.stdout.write(self.style.SUCCESS(f'Job #{job.pk} concluído.'))
                except Exception as exc:
                    self.stderr.write(self.style.ERROR(f'Job #{job.pk} falhou: {exc}'))
            elif once:
                break
            else:
                time.sleep(sleep_seconds)
