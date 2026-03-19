from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_or_update_admin(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@solufor.com',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'password': make_password('12345678'),
        },
    )

    if not created:
        user.email = 'admin@solufor.com'
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.password = make_password('12345678')
        user.save(update_fields=['email', 'is_staff', 'is_superuser', 'is_active', 'password'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_or_update_admin, migrations.RunPython.noop),
    ]
