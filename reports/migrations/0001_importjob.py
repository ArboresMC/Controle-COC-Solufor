from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import reports.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('participants', '0004_participant_performance_indexes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('workbook', models.FileField(upload_to=reports.models.import_workbook_path)),
                ('original_filename', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('processing', 'Processando'), ('completed', 'Concluído'), ('failed', 'Falhou')], db_index=True, default='pending', max_length=20)),
                ('summary', models.JSONField(blank=True, default=dict)),
                ('error_messages', models.JSONField(blank=True, default=list)),
                ('preview', models.JSONField(blank=True, default=dict)),
                ('progress_current', models.PositiveIntegerField(default=0)),
                ('progress_total', models.PositiveIntegerField(default=0)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('last_heartbeat', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_import_jobs', to=settings.AUTH_USER_MODEL)),
                ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='import_jobs', to='participants.participant')),
            ],
            options={
                'verbose_name': 'Job de importação',
                'verbose_name_plural': 'Jobs de importação',
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.AddIndex(
            model_name='importjob',
            index=models.Index(fields=['status', 'created_at'], name='reports_impo_status_0d3221_idx'),
        ),
        migrations.AddIndex(
            model_name='importjob',
            index=models.Index(fields=['participant', 'created_at'], name='reports_impo_partici_858c85_idx'),
        ),
        migrations.AddIndex(
            model_name='importjob',
            index=models.Index(fields=['created_by', 'created_at'], name='reports_impo_created_721566_idx'),
        ),
    ]
