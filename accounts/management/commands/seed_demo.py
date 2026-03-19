from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from participants.models import Participant
from catalog.models import Product, Counterparty
from transactions.models import EntryRecord, SaleRecord
from compliance.models import MonthlyClosing


class Command(BaseCommand):
    help = 'Cria dados demonstrativos e usuários prontos para uso.'

    def handle(self, *args, **options):
        User = get_user_model()

        participant, _ = Participant.objects.get_or_create(
            cnpj='12.345.678/0001-90',
            defaults={
                'legal_name': 'Madeireira Exemplo Ltda',
                'trade_name': 'Madeireira Exemplo',
                'contact_name': 'Ana Souza',
                'contact_email': 'ana@madeireiraexemplo.com.br',
                'contact_phone': '(41) 99999-0000',
                'status': 'active',
            },
        )

        product1, _ = Product.objects.get_or_create(
            name='Tábua de Pinus',
            defaults={
                'category': 'Madeira serrada',
                'unit': 'm3',
                'fsc_applicable': True,
                'default_claim': 'FSC Mix',
                'active': True,
            },
        )
        product2, _ = Product.objects.get_or_create(
            name='Caixa de Papelão',
            defaults={
                'category': 'Embalagem',
                'unit': 'un',
                'fsc_applicable': True,
                'default_claim': 'FSC Recycled',
                'active': True,
            },
        )

        supplier, _ = Counterparty.objects.get_or_create(
            name='Fornecedor Florestal SA',
            type='supplier',
            participant=None,
            defaults={'document_id': '11.111.111/0001-11'},
        )
        customer, _ = Counterparty.objects.get_or_create(
            name='Cliente Distribuidor Ltda',
            type='customer',
            participant=None,
            defaults={'document_id': '22.222.222/0001-22'},
        )

        manager, created = User.objects.get_or_create(
            username='gestor',
            defaults={
                'email': 'gestor@portal-fsc.local',
                'role': 'manager',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created or not manager.check_password('12345678'):
            manager.set_password('12345678')
            manager.save()

        participant_user, created = User.objects.get_or_create(
            username='participante',
            defaults={
                'email': 'participante@portal-fsc.local',
                'role': 'participant',
                'participant': participant,
                'is_staff': False,
            },
        )
        if participant_user.participant_id != participant.id:
            participant_user.participant = participant
        participant_user.role = 'participant'
        if created or not participant_user.check_password('12345678'):
            participant_user.set_password('12345678')
        participant_user.save()

        auditor, created = User.objects.get_or_create(
            username='auditor',
            defaults={
                'email': 'auditor@portal-fsc.local',
                'role': 'auditor',
                'is_staff': False,
            },
        )
        if created or not auditor.check_password('12345678'):
            auditor.set_password('12345678')
            auditor.save()

        today = date.today()
        entry_date = today - timedelta(days=3)
        sale_date = today - timedelta(days=1)

        EntryRecord.objects.get_or_create(
            participant=participant,
            movement_date=entry_date,
            document_number='NF-ENT-001',
            supplier=supplier,
            product=product1,
            defaults={
                'quantity': 12.5,
                'unit_snapshot': product1.unit,
                'fsc_claim': product1.default_claim,
                'batch_code': 'L-001',
                'notes': 'Lançamento de exemplo',
                'created_by': manager,
                'status': 'submitted',
            },
        )

        SaleRecord.objects.get_or_create(
            participant=participant,
            movement_date=sale_date,
            document_number='NF-SAI-001',
            customer=customer,
            product=product2,
            defaults={
                'quantity': 150,
                'unit_snapshot': product2.unit,
                'fsc_claim': product2.default_claim,
                'batch_code': 'CX-150',
                'notes': 'Venda de exemplo',
                'created_by': manager,
                'status': 'submitted',
            },
        )

        MonthlyClosing.objects.get_or_create(
            participant=participant,
            year=today.year,
            month=today.month,
            defaults={
                'status': 'open',
                'participant_notes': 'Fechamento ainda não enviado.',
            },
        )

        self.stdout.write(self.style.SUCCESS('Dados de demonstração criados.'))
        self.stdout.write('Usuários prontos:')
        self.stdout.write('  gestor / 12345678')
        self.stdout.write('  participante / 12345678')
        self.stdout.write('  auditor / 12345678')
