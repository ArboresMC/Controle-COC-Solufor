from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0003_add_missing_columns'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE compliance_monthlyclosing
              ALTER COLUMN manager_notes SET DEFAULT '',
              ALTER COLUMN participant_notes SET DEFAULT '';
            UPDATE compliance_monthlyclosing
              SET manager_notes = '' WHERE manager_notes IS NULL;
            UPDATE compliance_monthlyclosing
              SET participant_notes = '' WHERE participant_notes IS NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
