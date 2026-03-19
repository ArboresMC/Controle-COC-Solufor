from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_producttransformationrule_productunitconversion'),
        ('transactions', '0005_tracelot_fsc_claim'),
    ]

    operations = [
        migrations.AddField(
            model_name='salerecord',
            name='supplier',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name='sales_as_source_supplier',
                to='catalog.counterparty',
                verbose_name='Fornecedor de origem',
            ),
        ),
    ]
