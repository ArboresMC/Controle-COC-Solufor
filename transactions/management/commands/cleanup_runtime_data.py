from django.contrib.sessions.models import Session
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Limpa apenas dados técnicos seguros: sessões expiradas.'

    def handle(self, *args, **options):
        deleted_expired, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f'Sessões expiradas removidas: {deleted_expired}. Nenhum dado operacional foi apagado.'
            )
        )
