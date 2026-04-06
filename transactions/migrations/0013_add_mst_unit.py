from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adiciona Metro Estéreo (mst) como unidade de medida aceita
    em todas as tabelas que usam choices de unidade.
    """

    dependencies = [
        ('transactions', '0012_recreate_performance_indexes'),
    ]

    UNIT_CHOICES = [
        ('m3',  'm³'),
        ('kg',  'kg'),
        ('t',   't'),
        ('un',  'un'),
        ('mst', 'mst'),
    ]

    operations = [
        # EntryRecord
        migrations.AlterField(
            model_name='entryrecord',
            name='movement_unit',
            field=models.CharField(
                blank=True, choices=UNIT_CHOICES,
                max_length=10, verbose_name='Unidade informada',
            ),
        ),
        migrations.AlterField(
            model_name='entryrecord',
            name='unit_snapshot',
            field=models.CharField(
                choices=UNIT_CHOICES,
                max_length=10, verbose_name='Unidade base',
            ),
        ),
        # SaleRecord
        migrations.AlterField(
            model_name='salerecord',
            name='movement_unit',
            field=models.CharField(
                blank=True, choices=UNIT_CHOICES,
                max_length=10, verbose_name='Unidade informada',
            ),
        ),
        migrations.AlterField(
            model_name='salerecord',
            name='unit_snapshot',
            field=models.CharField(
                choices=UNIT_CHOICES,
                max_length=10, verbose_name='Unidade base',
            ),
        ),
        # TransformationRecord
        migrations.AlterField(
            model_name='transformationrecord',
            name='source_unit',
            field=models.CharField(
                choices=UNIT_CHOICES,
                max_length=10, verbose_name='Unidade origem informada',
            ),
        ),
        migrations.AlterField(
            model_name='transformationrecord',
            name='target_unit_snapshot',
            field=models.CharField(
                choices=UNIT_CHOICES,
                max_length=10, verbose_name='Unidade base destino',
            ),
        ),
        # TraceLot
        migrations.AlterField(
            model_name='tracelot',
            name='unit_snapshot',
            field=models.CharField(
                choices=UNIT_CHOICES,
                max_length=10, verbose_name='Unidade base',
            ),
        ),
    ]
