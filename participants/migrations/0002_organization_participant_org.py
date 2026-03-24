from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Nome do ambiente')),
                ('legal_name', models.CharField(blank=True, max_length=255, verbose_name='Razão social do ambiente')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='Slug')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Ambiente',
                'verbose_name_plural': 'Ambientes',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='participant',
            name='organization',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='participants',
                to='participants.organization',
                verbose_name='Ambiente',
            ),
        ),
    ]
