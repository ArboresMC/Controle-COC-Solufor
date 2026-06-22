from django.db import migrations
from django.contrib.auth.hashers import make_password


# (username, cnpj_do_participante, email)
USERS = [
    ("AFFleischer", "01.518.561/0001-40", "direcao@affleischer.com.br"),
    ("Alianca", "33.285.403/0001-83", "viviane@caraunomadeiras.com.br"),
    ("GFRibas", "32.973.986/0002-53", "guilherme@gfribas.com.br"),
    ("MLM", "57.724.904/0001-87", "karine@mouraforest.com.br"),
    ("MBR", "34.113.986/0001-28", "saionara_jf@hotmail.com"),
    ("Oyola", "05.860.493/0001-53", "roberto.oyola@gmail.com"),
    ("RHFlorestal", "57.605.384/0001-93", "hornungmadeiras@uol.com.br"),
    ("AESerrariaDelavi", "05.504.172/0001-16", "serrariadelavi@gmail.com"),
    ("Caravaggio", "29.036.044/0001-53", "caravaggioflorestal@caravaggioflorestal.com.br"),
    ("TimberTrade", "05.215.718/0001-19", "douglascarassa@hotmail.com"),
    ("Keijunior", "80.528.383/0001-04", "ravi.figueiredo@valeverdeflorestal.com"),
    ("LAServicos", "50.667.107/0001-66", "Higor.laservicosflorestais@gmail.com"),
    ("ItamadMatriz", "29.271.176/0001-60", "mflorestal2010@gmail.com"),
    ("ItamadFilial", "29.271.176/0002-40", "mflorestal2010@gmail.com"),
    ("MadeirasCom", "10.768.360/0001-91", "edecarlos.rech@terra.com.br"),
    ("MBRFilial", "34.113.986/0004-70", "saionara_jf@hotmail.com"),
    ("Cavassin", "22.010.114/0001-55", "madeirascavassin@hotmail.com"),
    ("Dirlei", "21.605.546/0001-46", "empresaademilsonpires@gmail.com"),
    ("Trentini", "17.467.420/0001-85", "administrativo@trentiniflorestal.com.br"),
    ("RRToniolo", "46.421.786/0001-11", ""),
]

DEFAULT_PASSWORD = "Solufor1@"


def bootstrap_participant_users(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    Participant = apps.get_model('participants', 'Participant')

    hashed_password = make_password(DEFAULT_PASSWORD)

    for username, cnpj, email in USERS:
        participant = Participant.objects.filter(cnpj=cnpj).first()
        if not participant:
            continue

        User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'role': 'participant',
                'organization': participant.organization,
                'participant': participant,
                'password': hashed_password,
                'is_active': True,
                'is_staff': False,
                'is_superuser': False,
                'must_change_password': True,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_fix_admin_password'),
        ('participants', '0006_bootstrap_participants'),
    ]

    operations = [
        migrations.RunPython(bootstrap_participant_users, migrations.RunPython.noop),
    ]
