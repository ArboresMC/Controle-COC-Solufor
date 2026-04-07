from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0002_monthlyclosing_v2'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE compliance_monthlyclosing
              ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              ADD COLUMN IF NOT EXISTS reviewed_by_id INTEGER NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
