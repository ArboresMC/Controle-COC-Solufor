from django.core.management.base import BaseCommand
from django.db import transaction
from transactions.models import EntryRecord, SaleRecord, TransformationRecord, TraceLot, LotAllocation
from transactions.services import sync_entry_lot, sync_transformation_target_lot, reallocate_sale, reallocate_transformation_sources


class Command(BaseCommand):
    help = 'Reconstrói lotes rastreáveis, alocações de transformações e vínculos compra-venda a partir dos lançamentos existentes.'

    def handle(self, *args, **options):
        with transaction.atomic():
            LotAllocation.objects.all().delete()
            TraceLot.objects.all().delete()

            for entry in EntryRecord.objects.select_related('participant', 'product', 'supplier').order_by('movement_date', 'id'):
                sync_entry_lot(entry)

            for transformation in TransformationRecord.objects.select_related('participant', 'source_product', 'target_product').order_by('movement_date', 'id'):
                reallocate_transformation_sources(transformation)
                sync_transformation_target_lot(transformation)

            for sale in SaleRecord.objects.select_related('participant', 'product', 'customer').order_by('movement_date', 'id'):
                reallocate_sale(sale)

        self.stdout.write(self.style.SUCCESS('Rastreabilidade reconstruída com sucesso.'))
