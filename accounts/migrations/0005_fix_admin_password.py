from django.db import migrations


def fix_admin_password(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        return
    # set_password() do model real (não do historical model) faz o hash corretamente
    from django.contrib.auth.hashers import make_password
    user.password = make_password('12345678')
    user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_backfill_user_organization'),
    ]

    operations = [
        migrations.RunPython(fix_admin_password, migrations.RunPython.noop),
    ]
