from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        # Ajuste para o nome real da sua migration anterior em compliance
        ('compliance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='monthlyclosing',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('open', 'Aberto'),
                    ('submitted', 'Aguardando aprovação'),
                    ('approved', 'Aprovado'),
                    ('rejected', 'Rejeitado'),
                ],
                default='open',
            ),
        ),
        migrations.AddField(
            model_name='monthlyclosing',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True, verbose_name='Motivo da rejeição'),
        ),
        migrations.AddField(
            model_name='monthlyclosing',
            name='submitted_at',
            field=models.DateTimeField(null=True, blank=True, verbose_name='Enviado em'),
        ),
        migrations.AddField(
            model_name='monthlyclosing',
            name='reviewed_at',
            field=models.DateTimeField(null=True, blank=True, verbose_name='Revisado em'),
        ),
        migrations.AddField(
            model_name='monthlyclosing',
            name='reviewed_by',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reviewed_closings',
                to='accounts.customuser',
                verbose_name='Revisado por',
            ),
        ),
    ]
