from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0003_backfill_existing_participants_to_default_org'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='participant',
            index=models.Index(fields=['organization', 'status'], name='part_org_status_idx'),
        ),
        migrations.AddIndex(
            model_name='participant',
            index=models.Index(fields=['organization', 'trade_name'], name='part_org_trade_idx'),
        ),
    ]
