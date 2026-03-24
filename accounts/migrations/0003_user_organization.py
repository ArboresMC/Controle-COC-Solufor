from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0002_organization_participant_org'),
        ('accounts', '0002_bootstrap_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='organization',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users',
                to='participants.organization',
            ),
        ),
    ]