from django.db import migrations


def create_or_update_admin(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@solufor.com',
            'role': 'manager',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'must_change_password': False,
        },
    )

    user.email = 'admin@solufor.com'
    user.role = 'manager'
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    if hasattr(user, 'must_change_password'):
        user.must_change_password = False
    user.set_password('12345678')
    user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_or_update_admin, migrations.RunPython.noop),
    ]
