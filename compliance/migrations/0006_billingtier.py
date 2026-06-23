# Generated manually on 2026-06-23

from django.db import migrations, models


# Faixas atuais (espelham o que estava hardcoded em
# transactions.views.BillingReportView antes desta migration).
# Formato: (ordem, limite_max_ou_None, valor)
SEED_COC = [
    (1, 20, 30),
    (2, 50, 70),
    (3, None, 120),
]
SEED_FM = [
    (1, 3, 25),
    (2, 10, 60),
    (3, 20, 110),
    (4, None, 180),
]


def seed_billing_tiers(apps, schema_editor):
    BillingTier = apps.get_model('compliance', 'BillingTier')
    for ordem, limite_max, valor in SEED_COC:
        BillingTier.objects.get_or_create(
            modulo='coc', ordem=ordem,
            defaults={'limite_max': limite_max, 'valor': valor},
        )
    for ordem, limite_max, valor in SEED_FM:
        BillingTier.objects.get_or_create(
            modulo='fm', ordem=ordem,
            defaults={'limite_max': limite_max, 'valor': valor},
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0005_alter_monthlyclosing_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillingTier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modulo', models.CharField(choices=[('coc', 'Cadeia de Custódia'), ('fm', 'Manejo Florestal')], max_length=10, verbose_name='Módulo')),
                ('ordem', models.PositiveIntegerField(verbose_name='Ordem da faixa')),
                ('limite_max', models.PositiveIntegerField(blank=True, help_text='Vazio significa "acima do limite anterior" (última faixa).', null=True, verbose_name='Limite máximo da faixa')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor mensal (R$)')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Faixa de Cobrança',
                'verbose_name_plural': 'Faixas de Cobrança',
                'ordering': ['modulo', 'ordem'],
                'unique_together': {('modulo', 'ordem')},
            },
        ),
        migrations.RunPython(seed_billing_tiers, noop_reverse),
    ]
