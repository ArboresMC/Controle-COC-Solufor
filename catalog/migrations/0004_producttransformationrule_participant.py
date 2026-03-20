from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0001_initial'),
        ('catalog', '0003_fscclaim'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttransformationrule',
            name='participant',
            field=models.ForeignKey(blank=True, help_text='Deixe em branco para usar como regra geral. Regras específicas do participante têm prioridade.', null=True, on_delete=models.deletion.CASCADE, related_name='transformation_rules', to='participants.participant', verbose_name='Participante'),
        ),
        migrations.AlterUniqueTogether(
            name='producttransformationrule',
            unique_together={('participant', 'source_product', 'target_product')},
        ),
    ]
