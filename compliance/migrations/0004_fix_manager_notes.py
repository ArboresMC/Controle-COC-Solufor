from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0003_add_missing_columns'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            DECLARE
                col text;
            BEGIN
                FOREACH col IN ARRAY ARRAY['manager_notes', 'participant_notes']
                LOOP
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'compliance_monthlyclosing'
                          AND column_name = col
                    ) THEN
                        EXECUTE format(
                            'ALTER TABLE compliance_monthlyclosing ALTER COLUMN %I SET DEFAULT ''''',
                            col
                        );
                        EXECUTE format(
                            'UPDATE compliance_monthlyclosing SET %I = '''' WHERE %I IS NULL',
                            col, col
                        );
                    END IF;
                END LOOP;
            END
            $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
