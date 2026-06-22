from django.db import migrations
from datetime import datetime, timezone as dt_timezone


PARTICIPANTS = [
    # (legal_name, trade_name, cnpj, contact_name, contact_phone, contact_email, status, created_date)
    ("A F Fleischer & Cia Ltda", "A F Fleischer", "01.518.561/0001-40", "Jaqueline", "(42) 9 9137 7660", "direcao@affleischer.com.br", "inactive", "2021-09-06"),
    ("Aliança Comércio de Madeiras LTDA (Matriz e Filial)", "Aliança Madeiras", "33.285.403/0001-83", "Viviane Pinto Pereira", "(54) 9 9982 4505", "viviane@caraunomadeiras.com.br", "active", "2024-08-05"),
    ("GFRibas Agroflorestal LTDA", "GFRibas Agroflorestal", "32.973.986/0002-53", "Cristiane", "(49) 9 9825 5418", "guilherme@gfribas.com.br", "inactive", "2024-11-14"),
    ("MLM Madeiras LTDA", "MLM Madeiras", "57.724.904/0001-87", "Karine", "(42) 9 9998 9444", "karine@mouraforest.com.br", "inactive", "2024-11-14"),
    ("MBR Transportes e Extração Florestal LTDA", "MBR Transportes", "34.113.986/0001-28", "Saionara Conti", "(48) 9 9695 1443", "saionara_jf@hotmail.com", "inactive", "2024-10-28"),
    ("Oyola Transportes Ltda", "Oyola Transportes", "05.860.493/0001-53", "Roberto", "(43) 9 9979 1850", "roberto.oyola@gmail.com", "active", "2022-03-10"),
    ("RH Florestal LTDA", "RH Florestal", "57.605.384/0001-93", "Micheli", "(42) 9 8832 6661", "hornungmadeiras@uol.com.br", "active", "2024-12-04"),
    ("AE Serraria Delavi", "AE Serraria Delavi", "05.504.172/0001-16", "Gustavo", "(51) 9 9995 2832", "serrariadelavi@gmail.com", "active", "2022-04-30"),
    ("Florestal Caravaggio S/A (Matriz e Filial)", "Florestal Caravaggio", "29.036.044/0001-53", "Gisele Meneghetti", "(54) 9 9276 8767", "caravaggioflorestal@caravaggioflorestal.com.br", "inactive", "2024-10-28"),
    ("Timber Trade Florestal EIRELI", "Timber Trade Florestal", "05.215.718/0001-19", "Douglas", "(42) 9 8411 6644", "douglascarassa@hotmail.com", "inactive", "2021-06-07"),
    ("Transportadora Keijunior LTDA", "Transportadora Keijunior", "80.528.383/0001-04", "Ravi Figueiredo", "(42) 9 9993 0006", "ravi.figueiredo@valeverdeflorestal.com", "active", "2022-03-07"),
    ("L.A. Serviços Florestais e Comércio de Madeiras LTDA", "L.A. Serviços Florestais", "50.667.107/0001-66", "Higor", "(15) 9 9689 3301", "Higor.laservicosflorestais@gmail.com", "active", "2025-07-04"),
    ("Itamad Transporte e Comércio de Madeiras LTDA (Matriz)", "Itamad Transporte (Matriz)", "29.271.176/0001-60", "Marcio", "(15) 9 9192 1816", "mflorestal2010@gmail.com", "inactive", "2025-07-04"),
    ("Itamad Transporte e Comércio de Madeiras LTDA (Filial)", "Itamad Transporte (Filial)", "29.271.176/0002-40", "Marcio", "(15) 9 9192 1816", "mflorestal2010@gmail.com", "inactive", "2025-07-31"),
    ("Madeiras.Com LTDA", "Madeiras.Com", "10.768.360/0001-91", "Edecarlos Rech", "(47) 9 8836-6319", "edecarlos.rech@terra.com.br", "inactive", "2025-12-11"),
    ("MBR Transportes e Extração Florestal LTDA (Filial)", "MBR Transportes (Filial)", "34.113.986/0004-70", "Saionara Conti", "(48) 9 9695 1443", "saionara_jf@hotmail.com", "inactive", "2025-12-11"),
    ("Cavassin Madeiras LTDA", "Cavassin Madeiras", "22.010.114/0001-55", "Eugênio Kordeiak", "(42) 9 9152 1662", "madeirascavassin@hotmail.com", "inactive", "2025-12-08"),
    ("Dirlei Gomes Pires Ltda", "Dirlei Gomes Pires", "21.605.546/0001-46", "Ademilson Pires", "(42) 9 9954 0809", "empresaademilsonpires@gmail.com", "active", "2026-04-22"),
    ("Trentini Comércio Florestal Ltda", "Trentini Florestal", "17.467.420/0001-85", "Rafael Freitas", "(15) 9 9778 4796", "administrativo@trentiniflorestal.com.br", "active", "2026-04-22"),
    ("RR Toniolo Reflorestamento e Extração de Madeiras Ltda", "RR Toniolo", "46.421.786/0001-11", "Jonathan", "(42) 9 9829 0841", "", "active", None),
]


def bootstrap_participants(apps, schema_editor):
    Organization = apps.get_model('participants', 'Organization')
    Participant = apps.get_model('participants', 'Participant')

    org = Organization.objects.first()
    if not org:
        org = Organization.objects.create(
            name='Solufor',
            slug='solufor',
            legal_name='Solufor Soluções Florestais',
            is_active=True,
        )

    for legal_name, trade_name, cnpj, contact_name, contact_phone, contact_email, status, created_date in PARTICIPANTS:
        participant, created = Participant.objects.get_or_create(
            cnpj=cnpj,
            defaults={
                'organization': org,
                'legal_name': legal_name,
                'trade_name': trade_name,
                'contact_name': contact_name,
                'contact_phone': contact_phone,
                'contact_email': contact_email,
                'status': status,
            }
        )
        if created and created_date:
            dt = datetime.strptime(created_date, '%Y-%m-%d').replace(tzinfo=dt_timezone.utc)
            Participant.objects.filter(pk=participant.pk).update(created_at=dt)


class Migration(migrations.Migration):

    dependencies = [
        ('participants', '0005_remove_participant_part_org_status_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(bootstrap_participants, migrations.RunPython.noop),
    ]
