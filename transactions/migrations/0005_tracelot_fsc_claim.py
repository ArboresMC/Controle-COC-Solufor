from django.db import migrations, models


def populate_trace_lot_claims(apps, schema_editor):
    TraceLot = apps.get_model('transactions', 'TraceLot')

    for lot in TraceLot.objects.select_related('entry').all():
        claim = ''
        if lot.entry_id and lot.entry and lot.entry.fsc_claim:
            claim = lot.entry.fsc_claim.strip()
        elif lot.transformation_id and getattr(lot, 'transformation', None):
            allocations = lot.transformation.source_lot_allocations.select_related('lot').all()
            claims = sorted({(allocation.lot.fsc_claim or '').strip() for allocation in allocations if (allocation.lot.fsc_claim or '').strip()})
            if len(claims) == 1:
                claim = claims[0]
        lot.fsc_claim = claim
        lot.save(update_fields=['fsc_claim'])


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0004_tracelot_lotallocation'),
        ('catalog', '0003_fscclaim'),
    ]

    operations = [
        migrations.AddField(
            model_name='tracelot',
            name='fsc_claim',
            field=models.CharField(blank=True, max_length=100, verbose_name='Declaração FSC'),
        ),
        migrations.RunPython(populate_trace_lot_claims, migrations.RunPython.noop),
    ]
