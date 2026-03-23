from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from django.db import transaction, models
from django.db.models import Sum
from catalog.models import ProductUnitConversion, ProductTransformationRule, Product
from .models import TraceLot, LotAllocation


UNIT_LABELS = dict(Product.UNIT_CHOICES)


def to_decimal(value):
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass
class TraceSource:
    product_id: int
    participant_id: int
    ref_type: str
    ref_id: int
    ref_label: str
    movement_date: object
    quantity_total: Decimal
    quantity_remaining: Decimal
    unit_label: str


def get_unit_conversion_factor(product, from_unit: str) -> Decimal:
    if not from_unit:
        raise ValueError('Unidade não informada.')
    base_unit = product.unit
    if from_unit == base_unit:
        return Decimal('1')
    conversion = ProductUnitConversion.objects.filter(
        product=product,
        from_unit=from_unit,
        to_unit=base_unit,
        active=True,
    ).first()
    if conversion:
        return conversion.factor
    reverse = ProductUnitConversion.objects.filter(
        product=product,
        from_unit=base_unit,
        to_unit=from_unit,
        active=True,
    ).first()
    if reverse and reverse.factor:
        return Decimal('1') / reverse.factor
    raise ValueError(f'Não existe fator de conversão cadastrado para {product} de {from_unit} para {base_unit}.')


def convert_to_base(product, quantity, from_unit: str) -> Decimal:
    quantity = to_decimal(quantity)
    factor = get_unit_conversion_factor(product, from_unit)
    return (quantity * factor).quantize(Decimal('0.001'))


def get_transformation_rule(source_product, target_product, participant=None):
    qs = ProductTransformationRule.objects.filter(
        source_product=source_product,
        target_product=target_product,
        active=True,
    )
    if participant is not None:
        specific = qs.filter(participant=participant).first()
        if specific:
            return specific
    return qs.filter(participant__isnull=True).first()


def calculate_target_from_source(source_product, target_product, source_quantity_base, participant=None):
    source_quantity_base = to_decimal(source_quantity_base)
    rule = get_transformation_rule(source_product, target_product, participant=participant)
    if not rule:
        raise ValueError('Não existe regra de transformação cadastrada para os produtos selecionados para esta empresa.')
    return (source_quantity_base * rule.yield_factor).quantize(Decimal('0.001'))


def _lot_allocated_total(lot):
    return to_decimal(lot.allocations.aggregate(total=Sum('quantity_base'))['total'])


def get_lot_remaining(lot):
    return (to_decimal(lot.quantity_base) - _lot_allocated_total(lot)).quantize(Decimal('0.001'))


def get_lot_remaining_for_sale(lot, sale=None):
    remaining = get_lot_remaining(lot)
    if sale and getattr(sale, 'pk', None):
        current = to_decimal(
            lot.allocations.filter(target_type='sale', sale=sale).aggregate(total=Sum('quantity_base'))['total']
        )
        remaining += current
    return remaining.quantize(Decimal('0.001'))


def get_lot_remaining_for_transformation(lot, transformation=None):
    remaining = get_lot_remaining(lot)
    if transformation and getattr(transformation, 'pk', None):
        current = to_decimal(
            lot.allocations.filter(target_type='transformation', transformation=transformation).aggregate(total=Sum('quantity_base'))['total']
        )
        remaining += current
    return remaining.quantize(Decimal('0.001'))


def _normalize_claim(value):
    return (value or '').strip()


def sync_entry_lot(entry):
    lot, _ = TraceLot.objects.get_or_create(
        entry=entry,
        defaults={
            'participant': entry.participant,
            'product': entry.product,
            'source_type': 'entry',
            'supplier': entry.supplier,
            'fsc_claim': entry.fsc_claim,
            'movement_date': entry.movement_date,
            'quantity_base': entry.quantity_base,
            'unit_snapshot': entry.unit_snapshot,
        },
    )
    allocated = _lot_allocated_total(lot)
    if allocated > to_decimal(entry.quantity_base):
        raise ValueError(f'A entrada {entry.document_number} já possui {allocated} {entry.get_unit_snapshot_display()} rastreados. Não é possível reduzir abaixo desse valor.')
    lot.participant = entry.participant
    lot.product = entry.product
    lot.source_type = 'entry'
    lot.supplier = entry.supplier
    lot.fsc_claim = entry.fsc_claim
    lot.movement_date = entry.movement_date
    lot.quantity_base = entry.quantity_base
    lot.unit_snapshot = entry.unit_snapshot
    lot.save()
    return lot


def sync_transformation_target_lot(transformation):
    lot, _ = TraceLot.objects.get_or_create(
        transformation=transformation,
        defaults={
            'participant': transformation.participant,
            'product': transformation.target_product,
            'source_type': 'transformation',
            'movement_date': transformation.movement_date,
            'quantity_base': transformation.target_quantity_base,
            'unit_snapshot': transformation.target_unit_snapshot,
        },
    )
    allocated = _lot_allocated_total(lot)
    if allocated > to_decimal(transformation.target_quantity_base):
        raise ValueError(
            f'A transformação #{transformation.id} já possui {allocated} {transformation.target_product.get_unit_display()} consumidos em saídas. Não é possível reduzir a produção abaixo desse valor.'
        )

    source_allocations = list(transformation.source_lot_allocations.select_related('lot', 'lot__supplier').all())
    source_claims = sorted({(allocation.lot.fsc_claim or '').strip() for allocation in source_allocations if (allocation.lot.fsc_claim or '').strip()})
    if len(source_claims) > 1:
        raise ValueError('A transformação não pode consumir lotes com declarações FSC diferentes.')
    source_suppliers = sorted({allocation.lot.supplier_id for allocation in source_allocations if allocation.lot.supplier_id})
    if len(source_suppliers) > 1:
        raise ValueError('A transformação não pode consumir lotes de fornecedores diferentes.')

    inherited_supplier = source_allocations[0].lot.supplier if source_allocations and source_allocations[0].lot.supplier_id else None
    inherited_claim = source_claims[0] if len(source_claims) == 1 else ''

    lot.participant = transformation.participant
    lot.product = transformation.target_product
    lot.source_type = 'transformation'
    lot.supplier = inherited_supplier
    lot.fsc_claim = inherited_claim
    lot.movement_date = transformation.movement_date
    lot.quantity_base = transformation.target_quantity_base
    lot.unit_snapshot = transformation.target_unit_snapshot
    lot.save()
    return lot


def sync_transformation_metadata(transformation):
    source_allocations = list(transformation.source_lot_allocations.select_related('lot', 'lot__supplier').all())
    source_claims = sorted({(allocation.lot.fsc_claim or '').strip() for allocation in source_allocations if (allocation.lot.fsc_claim or '').strip()})
    if len(source_claims) > 1:
        raise ValueError('A transformação não pode consumir lotes com declarações FSC diferentes.')
    source_suppliers = sorted({allocation.lot.supplier_id for allocation in source_allocations if allocation.lot.supplier_id})
    if len(source_suppliers) > 1:
        raise ValueError('A transformação não pode consumir lotes de fornecedores diferentes.')

    transformation.supplier = source_allocations[0].lot.supplier if source_allocations and source_allocations[0].lot.supplier_id else None
    transformation.fsc_claim = source_claims[0] if len(source_claims) == 1 else ''
    transformation.save(update_fields=['supplier', 'fsc_claim'])
    return transformation


def _available_lots(participant, product, *, sale=None, include_lot_ids=None, fsc_claim=None, supplier=None):
    lots = TraceLot.objects.filter(participant=participant, product=product)
    if fsc_claim:
        lots = lots.filter(fsc_claim=fsc_claim)
    if supplier is not None:
        lots = lots.filter(supplier=supplier)
    lots = lots.order_by('movement_date', 'id')
    if include_lot_ids:
        lots = lots | TraceLot.objects.filter(pk__in=include_lot_ids, participant=participant, product=product)
        lots = lots.order_by('movement_date', 'id')
    items = []
    seen = set()
    for lot in lots:
        if lot.id in seen:
            continue
        seen.add(lot.id)
        remaining = get_lot_remaining_for_sale(lot, sale=sale) if sale else get_lot_remaining(lot)
        if remaining > 0:
            items.append((lot, remaining))
    return items


def get_manual_sale_lot_choices(participant, product=None, sale=None, fsc_claim=None):
    current_ids = []
    if sale and getattr(sale, 'pk', None):
        current_ids = list(sale.lot_allocations.values_list('lot_id', flat=True))

    qs = TraceLot.objects.filter(participant=participant)
    if fsc_claim:
        qs = qs.filter(fsc_claim=fsc_claim)
    if product:
        qs = qs.filter(models.Q(product=product) | models.Q(pk__in=current_ids))
    elif current_ids:
        qs = qs.filter(models.Q(pk__in=current_ids) | models.Q())

    qs = qs.select_related('product', 'supplier', 'entry', 'transformation').order_by('movement_date', 'id')

    lots = []
    for lot in qs:
        remaining = get_lot_remaining_for_sale(lot, sale=sale)
        if remaining <= 0:
            continue
        supplier_label, source_label = describe_lot_origins(lot)
        lots.append({
            'lot': lot,
            'remaining': remaining.quantize(Decimal('0.001')),
            'supplier': supplier_label,
            'source_label': source_label,
            'unit': lot.product.get_unit_display(),
        })
    return lots


def get_manual_transformation_lot_choices(participant, transformation=None, product=None):
    current_ids = []
    if transformation and getattr(transformation, 'pk', None):
        current_ids = list(transformation.source_lot_allocations.values_list('lot_id', flat=True))

    qs = TraceLot.objects.filter(participant=participant, source_type='entry')
    if product:
        qs = qs.filter(models.Q(product=product) | models.Q(pk__in=current_ids))
    elif current_ids:
        qs = qs.filter(models.Q(pk__in=current_ids) | models.Q())

    qs = qs.select_related('product', 'supplier', 'entry').order_by('movement_date', 'id')

    lots = []
    for lot in qs:
        remaining = get_lot_remaining_for_transformation(lot, transformation=transformation)
        if remaining <= 0:
            continue
        supplier_label, source_label = describe_lot_origins(lot)
        lots.append({
            'lot': lot,
            'remaining': remaining.quantize(Decimal('0.001')),
            'supplier': supplier_label,
            'source_label': source_label,
            'unit': lot.product.get_unit_display(),
        })
    return lots


def allocate_quantity_to_lots(participant, product, quantity_base, *, sale=None, transformation=None, preferred_lot=None, fsc_claim=None):
    qty_needed = to_decimal(quantity_base)
    if qty_needed <= 0:
        return []
    allocations = []
    selected_supplier = None
    selected_claim = _normalize_claim(fsc_claim)

    if preferred_lot is not None:
        if preferred_lot.participant_id != participant.id or preferred_lot.product_id != product.id:
            raise ValueError('O lote selecionado não pertence ao participante ou produto informado.')
        if selected_claim and _normalize_claim(getattr(preferred_lot, 'fsc_claim', '')) != selected_claim:
            raise ValueError('O lote selecionado possui declaração FSC diferente da informada na saída.')
        remaining = get_lot_remaining_for_sale(preferred_lot, sale=sale) if sale else get_lot_remaining(preferred_lot)
        if remaining < qty_needed:
            raise ValueError(
                f'Lote selecionado sem saldo suficiente. Disponível neste lote: {remaining.quantize(Decimal("0.001"))} {product.get_unit_display()}.'
            )
        selected_supplier = preferred_lot.supplier
        selected_claim = _normalize_claim(preferred_lot.fsc_claim)
        allocation = LotAllocation.objects.create(
            participant=participant,
            lot=preferred_lot,
            sale=sale,
            transformation=transformation,
            target_type='sale' if sale else 'transformation',
            quantity_base=qty_needed.quantize(Decimal('0.001')),
        )
        if sale is not None:
            sale.supplier = selected_supplier
            sale.fsc_claim = selected_claim
            sale.save(update_fields=['supplier', 'fsc_claim'])
        return [allocation]

    for lot, remaining in _available_lots(participant, product, sale=sale, fsc_claim=selected_claim or None):
        if qty_needed <= 0:
            break
        lot_claim = _normalize_claim(lot.fsc_claim)
        if selected_claim and lot_claim != selected_claim:
            continue
        if not selected_claim:
            selected_claim = lot_claim
        if selected_supplier is None:
            selected_supplier = lot.supplier
        elif lot.supplier_id != getattr(selected_supplier, 'id', None):
            raise ValueError('A saída não pode consumir lotes de fornecedores diferentes.')
        if selected_claim and lot_claim != selected_claim:
            raise ValueError('A saída não pode consumir lotes com declarações FSC diferentes.')
        consumed = min(remaining, qty_needed)
        allocation = LotAllocation.objects.create(
            participant=participant,
            lot=lot,
            sale=sale,
            transformation=transformation,
            target_type='sale' if sale else 'transformation',
            quantity_base=consumed.quantize(Decimal('0.001')),
        )
        allocations.append(allocation)
        qty_needed -= consumed
    if sale is not None:
        sale.supplier = selected_supplier
        sale.fsc_claim = selected_claim or ''
        sale.save(update_fields=['supplier', 'fsc_claim'])

    if qty_needed > 0:
        if sale:
            target_desc = f'saída {sale.document_number}'
        else:
            target_desc = f'transformação #{transformation.id if transformation and transformation.id else "nova"}'
        raise ValueError(
            f'Não existe saldo rastreável suficiente para {target_desc}. Faltam {qty_needed.quantize(Decimal("0.001"))} {product.get_unit_display()}.'
        )
    return allocations


@transaction.atomic
def reallocate_sale(sale, preferred_lot=None):
    sale.lot_allocations.all().delete()
    sale.supplier = None
    sale.save(update_fields=['supplier'])
    return allocate_quantity_to_lots(
        sale.participant,
        sale.product,
        sale.quantity_base,
        sale=sale,
        preferred_lot=preferred_lot,
        fsc_claim=sale.fsc_claim,
    )


@transaction.atomic
def reallocate_transformation_sources(transformation, preferred_lot=None):
    transformation.source_lot_allocations.all().delete()
    return allocate_quantity_to_lots(
        transformation.participant,
        transformation.source_product,
        transformation.source_quantity_base,
        transformation=transformation,
        preferred_lot=preferred_lot,
    )


def get_available_balance(participant, product, statuses=None):
    lots = TraceLot.objects.filter(participant=participant, product=product)
    total = Decimal('0')
    for lot in lots:
        if lot.entry_id and statuses is not None and lot.entry.status not in statuses:
            continue
        if lot.transformation_id and statuses is not None:
            pass
        total += get_lot_remaining(lot)
    return total.quantize(Decimal('0.001'))


def get_balance_items(participant, projected=False):
    statuses = None if projected else ['reviewed']
    items = []
    for product in Product.objects.filter(active=True).order_by('name'):
        available = get_available_balance(participant, product, statuses=statuses)
        if available != 0:
            items.append({
                'product': product,
                'balance': available,
                'unit': product.get_unit_display(),
                'status_class': classify_balance(available),
            })
    return items


def classify_balance(value):
    value = to_decimal(value)
    if value <= Decimal('1'):
        return 'danger'
    if value <= Decimal('5'):
        return 'warning'
    return 'success'


def get_participant_balance_summary(participant):
    balances = get_balance_items(participant, projected=True)
    total_items = len(balances)
    total_low = len([b for b in balances if b['status_class'] in ['warning', 'danger']])
    return {
        'participant': participant,
        'balances': balances,
        'balance_count': total_items,
        'low_count': total_low,
    }


def _origin_entry_ids_for_lot(lot, visited=None):
    visited = visited or set()
    key = f'lot:{lot.id}'
    if key in visited:
        return set()
    visited.add(key)
    if lot.entry_id:
        return {lot.entry_id}
    if lot.transformation_id:
        entry_ids = set()
        for allocation in lot.transformation.source_lot_allocations.select_related('lot'):
            entry_ids.update(_origin_entry_ids_for_lot(allocation.lot, visited))
        return entry_ids
    return set()


def describe_lot_origins(lot):
    if lot.entry_id:
        supplier = str(lot.supplier) if lot.supplier_id else 'Sem fornecedor'
        return supplier, lot.label
    entry_ids = _origin_entry_ids_for_lot(lot)
    if not entry_ids:
        return 'Sem origem identificada', lot.label
    from .models import EntryRecord
    entries = EntryRecord.objects.select_related('supplier').filter(id__in=entry_ids)
    suppliers = sorted({str(e.supplier) for e in entries if e.supplier_id})
    supplier_label = ', '.join(suppliers) if suppliers else 'Sem fornecedor'
    source_label = f'{lot.label} · origens: ' + ', '.join(sorted({e.document_number for e in entries}))
    return supplier_label, source_label


def build_traceability_rows(participant=None, product=None):
    allocations = LotAllocation.objects.select_related(
        'participant', 'lot', 'lot__product', 'lot__supplier', 'sale', 'sale__customer',
        'transformation', 'transformation__target_product'
    ).order_by('lot__movement_date', 'lot__id', 'id')
    if participant:
        allocations = allocations.filter(participant=participant)
    if product:
        allocations = allocations.filter(lot__product=product)

    rows = []
    for allocation in allocations:
        supplier_label, source_label = describe_lot_origins(allocation.lot)
        if allocation.sale_id:
            use_type = 'saída'
            use_label = f'Saída {allocation.sale.document_number}'
            counterparty = str(allocation.sale.customer)
            destination_label = str(allocation.sale.product)
            use_date = allocation.sale.movement_date
        else:
            use_type = 'transformação/saída'
            doc = allocation.transformation.document_number or f'Transformação #{allocation.transformation_id}'
            use_label = doc
            counterparty = str(allocation.transformation.customer) if allocation.transformation.customer_id else 'Processo interno'
            destination_label = str(allocation.transformation.target_product)
            use_date = allocation.transformation.movement_date
        rows.append({
            'participant': allocation.participant,
            'product': allocation.lot.product,
            'use_type': use_type,
            'use_label': use_label,
            'use_date': use_date,
            'source_label': source_label,
            'source_date': allocation.lot.movement_date,
            'quantity': allocation.quantity_base.quantize(Decimal('0.001')),
            'unit': allocation.lot.product.get_unit_display(),
            'supplier': supplier_label,
            'counterparty': counterparty,
            'destination_label': destination_label,
        })
    return rows


def get_entry_balance_rows(participant=None):
    lots = TraceLot.objects.select_related('participant', 'product', 'supplier', 'entry').filter(source_type='entry').order_by('movement_date', 'id')
    if participant:
        lots = lots.filter(participant=participant)
    rows = []
    for lot in lots:
        sales_total = to_decimal(lot.allocations.filter(target_type='sale').aggregate(total=Sum('quantity_base'))['total'])
        transformations_total = to_decimal(lot.allocations.filter(target_type='transformation').aggregate(total=Sum('quantity_base'))['total'])
        customers = ', '.join(sorted({str(a.sale.customer) for a in lot.allocations.select_related('sale__customer').filter(target_type='sale', sale__customer__isnull=False)}))
        rows.append({
            'participant': lot.participant,
            'entry': lot.entry,
            'supplier': lot.supplier,
            'product': lot.product,
            'movement_date': lot.movement_date,
            'quantity_total': to_decimal(lot.quantity_base).quantize(Decimal('0.001')),
            'quantity_sold': sales_total.quantize(Decimal('0.001')),
            'quantity_transformed': transformations_total.quantize(Decimal('0.001')),
            'quantity_remaining': get_lot_remaining(lot),
            'unit': lot.product.get_unit_display(),
            'customers': customers,
        })
    return rows


def get_participant_alerts(participant, *, today=None):
    from datetime import date
    from compliance.models import MonthlyClosing
    from .models import EntryRecord, SaleRecord, TransformationRecord

    today = today or date.today()
    alerts = []
    low_balances = [b for b in get_balance_items(participant, projected=True) if b['status_class'] in ['warning', 'danger']]
    if low_balances:
        sample = ', '.join([f"{item['product']} ({item['balance']} {item['unit']})" for item in low_balances[:3]])
        alerts.append({
            'level': 'warning' if any(i['status_class']=='warning' for i in low_balances) else 'danger',
            'title': 'Saldos em atenção',
            'description': f'Itens com saldo baixo ou crítico: {sample}.',
            'url': '/',
        })

    corrections = EntryRecord.objects.filter(participant=participant, status='needs_correction').count() + SaleRecord.objects.filter(participant=participant, status='needs_correction').count()
    if corrections:
        alerts.append({
            'level': 'danger',
            'title': 'Pendências de correção',
            'description': f'Existem {corrections} lançamentos aguardando correção ou revisão.',
            'url': '/',
        })

    movement_exists = EntryRecord.objects.filter(participant=participant, movement_date__year=today.year, movement_date__month=today.month).exists() or SaleRecord.objects.filter(participant=participant, movement_date__year=today.year, movement_date__month=today.month).exists() or TransformationRecord.objects.filter(participant=participant, movement_date__year=today.year, movement_date__month=today.month).exists()
    if not movement_exists:
        alerts.append({
            'level': 'info',
            'title': 'Sem movimentação no mês atual',
            'description': 'Nenhuma entrada, saída ou transformação foi registrada nesta competência.',
            'url': '/compliance/',
        })

    current_closing = MonthlyClosing.objects.filter(participant=participant, year=today.year, month=today.month).first()
    if not current_closing:
        alerts.append({
            'level': 'warning',
            'title': 'Fechamento mensal pendente',
            'description': 'Ainda não existe fechamento aberto/enviado para o mês atual.',
            'url': '/compliance/',
        })
    elif current_closing.status in ['open', 'rejected', 'overdue']:
        alerts.append({
            'level': 'warning' if current_closing.status != 'rejected' else 'danger',
            'title': 'Fechamento mensal exige ação',
            'description': f'Situação atual: {current_closing.get_status_display()}. Revise os lançamentos e conclua o fechamento.',
            'url': '/compliance/',
        })
    return alerts


def get_manager_alerts(*, today=None):
    from datetime import date
    from compliance.models import MonthlyClosing
    from participants.models import Participant
    from .models import EntryRecord, SaleRecord

    today = today or date.today()
    alerts = []
    active_participants = Participant.objects.filter(status='active')
    closings = MonthlyClosing.objects.filter(year=today.year, month=today.month)
    without_closing = active_participants.exclude(id__in=closings.values_list('participant_id', flat=True))
    if without_closing.exists():
        alerts.append({
            'level': 'warning',
            'title': 'Participantes sem fechamento',
            'description': f'{without_closing.count()} participante(s) ainda sem fechamento na competência atual.',
            'url': '/compliance/manager/',
        })

    corrections = EntryRecord.objects.filter(status='needs_correction').count() + SaleRecord.objects.filter(status='needs_correction').count()
    if corrections:
        alerts.append({
            'level': 'danger',
            'title': 'Pendências de revisão',
            'description': f'Existem {corrections} lançamentos aguardando correção ou validação da gestão.',
            'url': '/transactions/manager/review/entries/',
        })

    no_movement = []
    for participant in active_participants:
        movement_exists = EntryRecord.objects.filter(participant=participant, movement_date__year=today.year, movement_date__month=today.month).exists() or SaleRecord.objects.filter(participant=participant, movement_date__year=today.year, movement_date__month=today.month).exists()
        if not movement_exists:
            no_movement.append(participant)
    if no_movement:
        alerts.append({
            'level': 'info',
            'title': 'Participantes sem movimento',
            'description': f'{len(no_movement)} participante(s) ainda sem compras ou vendas registradas no mês atual.',
            'url': '/',
        })

    low_participants = []
    for participant in active_participants:
        low_count = len([b for b in get_balance_items(participant, projected=True) if b['status_class'] in ['warning', 'danger']])
        if low_count:
            low_participants.append((participant, low_count))
    if low_participants:
        sample = ', '.join([f'{p} ({c})' for p,c in low_participants[:4]])
        alerts.append({
            'level': 'warning',
            'title': 'Saldos em atenção no grupo',
            'description': f'Participantes com itens em atenção: {sample}.',
            'url': '/',
        })
    return alerts
