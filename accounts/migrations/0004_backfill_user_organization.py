from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Participant = apps.get_model('participants', 'Participant')
    Organization = apps.get_model('participants', 'Organization')

    default_org = Organization.objects.filter(slug='ambiente-principal').first()
    participant_org_map = {
        p.id: p.organization_id
        for p in Participant.objects.exclude(organization__isnull=True).only('id', 'organization_id')
    }

    for user in User.objects.all().iterator():
        org_id = None
        if user.participant_id:
            org_id = participant_org_map.get(user.participant_id)
        if not org_id and default_org:
            org_id = default_org.id
        if org_id and user.organization_id != org_id:
            user.organization_id = org_id
            user.save(update_fields=['organization'])


def backwards(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.all().update(organization=None)


class Migration(migrations.Migration):

  dependencies = [
    ('participants', '0003_backfill_existing_participants_to_default_org'),
    ('accounts', '0003_user_organization'),
]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
