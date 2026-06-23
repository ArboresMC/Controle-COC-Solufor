from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Índices de performance para as queries mais frequentes do módulo de
    Manejo Florestal (Painel Manejo, listagem de entradas, dropdown de saída).
    """

    dependencies = [
        ('manejo', '0004_ajustes_historicos_fm'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='propriedade',
            index=models.Index(fields=['participant', 'ativa'], name='manejo_prop_part_ativa_idx'),
        ),
        migrations.AddIndex(
            model_name='inventarioentrada',
            index=models.Index(fields=['participant', '-data'], name='manejo_entrada_part_data_idx'),
        ),
        migrations.AddIndex(
            model_name='saidamanejo',
            index=models.Index(fields=['participant', '-data'], name='manejo_saida_part_data_idx'),
        ),
        migrations.AddIndex(
            model_name='saidamanejo',
            index=models.Index(fields=['entrada'], name='manejo_saida_entrada_idx'),
        ),
    ]
