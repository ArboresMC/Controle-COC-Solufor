from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='compliance_monthlyclosing' AND column_name='status'
                ) THEN
                    ALTER TABLE compliance_monthlyclosing
                    ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'open';
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='compliance_monthlyclosing' AND column_name='rejection_reason'
                ) THEN
                    ALTER TABLE compliance_monthlyclosing
                    ADD COLUMN rejection_reason TEXT NULL;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='compliance_monthlyclosing' AND column_name='submitted_at'
                ) THEN
                    ALTER TABLE compliance_monthlyclosing
                    ADD COLUMN submitted_at TIMESTAMPTZ NULL;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='compliance_monthlyclosing' AND column_name='reviewed_at'
                ) THEN
                    ALTER TABLE compliance_monthlyclosing
                    ADD COLUMN reviewed_at TIMESTAMPTZ NULL;
                END IF;

                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='compliance_monthlyclosing' AND column_name='reviewed_by_id'
                ) THEN
                    ALTER TABLE compliance_monthlyclosing
                    ADD COLUMN reviewed_by_id INTEGER NULL;
                END IF;
            END
            $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name='monthlyclosing',
                    name='submitted_at',
                    field=models.DateTimeField(null=True, blank=True),
                ),
                migrations.AddField(
                    model_name='monthlyclosing',
                    name='reviewed_at',
                    field=models.DateTimeField(null=True, blank=True),
                ),
                migrations.AddField(
                    model_name='monthlyclosing',
                    name='reviewed_by',
                    field=models.ForeignKey(
                        null=True,
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='reviewed_closings',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
