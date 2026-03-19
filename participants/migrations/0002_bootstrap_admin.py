from django.db import migrations


def create_admin(apps, schema_editor):
    User = apps.get_model('auth', 'User')

    user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@solufor.com',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        },
    )

    user.email = 'admin@solufor.com'
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password('12345678')
    user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_admin, migrations.RunPython.noop),
    ]
