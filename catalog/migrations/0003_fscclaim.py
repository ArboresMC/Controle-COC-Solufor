from django.db import migrations, models
from django.utils.text import slugify


DEFAULT_CLAIMS = [
    ('FSC 100%', 'fsc-100', 10),
    ('FSC Mix', 'fsc-mix', 20),
    ('FSC Recycled', 'fsc-recycled', 30),
    ('Controlled Wood', 'controlled-wood', 40),
    ('Madeira Controlada FSC', 'madeira-controlada-fsc', 50),
    ('Não FSC', 'nao-fsc', 60),
]


def seed_fsc_claims(apps, schema_editor):
    FSCClaim = apps.get_model('catalog', 'FSCClaim')
    EntryRecord = apps.get_model('transactions', 'EntryRecord')
    SaleRecord = apps.get_model('transactions', 'SaleRecord')

    seen_codes = set(FSCClaim.objects.values_list('code', flat=True))

    for name, code, sort_order in DEFAULT_CLAIMS:
        obj = FSCClaim.objects.filter(name=name).first()
        if obj:
            changed = False
            if not obj.code:
                obj.code = code
                changed = True
            if obj.sort_order != sort_order:
                obj.sort_order = sort_order
                changed = True
            if not obj.active:
                obj.active = True
                changed = True
            if changed:
                obj.save(update_fields=['code', 'sort_order', 'active'])
            seen_codes.add(obj.code)
        else:
            final_code = code
            base_code = code
            index = 1
            while FSCClaim.objects.filter(code=final_code).exists():
                suffix = f'-{index}'
                final_code = f'{base_code[:50-len(suffix)]}{suffix}'
                index += 1

            FSCClaim.objects.create(
                name=name,
                code=final_code,
                active=True,
                sort_order=sort_order,
            )
            seen_codes.add(final_code)

    names = set(
        value.strip()
        for value in EntryRecord.objects.exclude(fsc_claim='').values_list('fsc_claim', flat=True)
        if value and value.strip()
    )
    names.update(
        value.strip()
        for value in SaleRecord.objects.exclude(fsc_claim='').values_list('fsc_claim', flat=True)
        if value and value.strip()
    )

    sort_order = 100
    for name in sorted(names):
        existing = FSCClaim.objects.filter(name=name).first()
        if existing:
            continue

        code = slugify(name)[:50] or f'claim-{sort_order}'
        base_code = code
        index = 1
        while code in seen_codes or FSCClaim.objects.filter(code=code).exists():
            suffix = f'-{index}'
            code = f'{base_code[:50-len(suffix)]}{suffix}'
            index += 1

        FSCClaim.objects.create(
            name=name,
            code=code,
            active=True,
            sort_order=sort_order,
        )
        seen_codes.add(code)
        sort_order += 10


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0002_producttransformationrule_productunitconversion'),
        ('transactions', '0004_tracelot_lotallocation'),
    ]

    operations = [
        migrations.CreateModel(
            name='FSCClaim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Declaração FSC')),
                ('code', models.SlugField(max_length=50, unique=True, verbose_name='Código')),
                ('active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
            ],
            options={
                'verbose_name': 'Declaração FSC',
                'verbose_name_plural': 'Declarações FSC',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.RunPython(seed_fsc_claims, migrations.RunPython.noop),
    ]
