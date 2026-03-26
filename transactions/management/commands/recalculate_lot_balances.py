from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum

from transactions.models import TraceLot


class Command(BaseCommand):
    help = 'Recalcula o saldo disponível de todos os lotes rastreáveis.'

    def handle(self, *args, **options):
        total = 0
        for lot in TraceLot.objects.all().prefetch_related('allocations'):
            allocated = lot.allocations.aggregate(total=Sum('quantity_base'))['total'] or Decimal('0')
            available = (Decimal(str(lot.quantity_base)) - Decimal(str(allocated))).quantize(Decimal('0.001'))
            if lot.quantity_available != available:
                lot.quantity_available = available
                lot.save(update_fields=['quantity_available'])
                total += 1
        self.stdout.write(self.style.SUCCESS(f'Saldos recalculados: {total} lote(s) atualizados.'))
