from decimal import Decimal

from django.db import migrations, models
from django.db.models import Sum


def backfill_quantity_available(apps, schema_editor):
    TraceLot = apps.get_model('transactions', 'TraceLot')
    LotAllocation = apps.get_model('transactions', 'LotAllocation')
    for lot in TraceLot.objects.all():
        allocated = LotAllocation.objects.filter(lot_id=lot.id).aggregate(total=Sum('quantity_base'))['total'] or Decimal('0')
        lot.quantity_available = (Decimal(str(lot.quantity_base)) - Decimal(str(allocated))).quantize(Decimal('0.001'))
        lot.save(update_fields=['quantity_available'])


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0009_performance_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='tracelot',
            name='quantity_available',
            field=models.DecimalField(db_index=True, decimal_places=3, default=0, max_digits=14, verbose_name='Saldo disponível'),
        ),
        migrations.AddIndex(
            model_name='tracelot',
            index=models.Index(fields=['participant', 'product', 'quantity_available'], name='txn_lot_part_prod_av_idx'),
        ),
        migrations.AddIndex(
            model_name='lotallocation',
            index=models.Index(fields=['participant', 'lot', 'target_type'], name='txn_alloc_part_lot_target_idx'),
        ),
        migrations.RunPython(backfill_quantity_available, migrations.RunPython.noop),
    ]
