from django.db import migrations


def forwards(apps, schema_editor):
    Organization = apps.get_model('participants', 'Organization')
    Participant = apps.get_model('participants', 'Participant')

    org, _ = Organization.objects.get_or_create(
        slug='ambiente-principal',
        defaults={
            'name': 'Ambiente Principal',
            'legal_name': 'Ambiente Principal',
            'is_active': True,
        },
    )
    Participant.objects.filter(organization__isnull=True).update(organization=org)


def backwards(apps, schema_editor):
    Participant = apps.get_model('participants', 'Participant')
    Participant.objects.all().update(organization=None)


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0002_organization_participant_org'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
