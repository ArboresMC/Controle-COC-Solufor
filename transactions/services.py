from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from django.db.models import Sum
from catalog.models import ProductUnitConversion, ProductTransformationRule, Product


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



def get_transformation_rule(source_product, target_product):
    return ProductTransformationRule.objects.filter(
        source_product=source_product,
        target_product=target_product,
        active=True,
    ).first()



def calculate_target_from_source(source_product, target_product, source_quantity_base):
    source_quantity_base = to_decimal(source_quantity_base)
    rule = get_transformation_rule(source_product, target_product)
    if not rule:
        raise ValueError('Não existe regra de transformação cadastrada para os produtos selecionados.')
    return (source_quantity_base * rule.yield_factor).quantize(Decimal('0.001'))



def _movement_filters(prefix: str, statuses=None):
    kwargs = {}
    if statuses is not None:
        kwargs[f'{prefix}status__in'] = statuses
    return kwargs



def get_available_balance(participant, product, statuses=None):
    from .models import EntryRecord, SaleRecord, TransformationRecord

    entry_filter = {'participant': participant, 'product': product}
    sale_filter = {'participant': participant, 'product': product}
    if statuses is not None:
        entry_filter['status__in'] = statuses
        sale_filter['status__in'] = statuses

    entries = EntryRecord.objects.filter(**entry_filter).aggregate(total=Sum('quantity_base'))['total'] or Decimal('0')
    sales = SaleRecord.objects.filter(**sale_filter).aggregate(total=Sum('quantity_base'))['total'] or Decimal('0')
    produced = TransformationRecord.objects.filter(participant=participant, target_product=product).aggregate(total=Sum('target_quantity_base'))['total'] or Decimal('0')
    consumed = TransformationRecord.objects.filter(participant=participant, source_product=product).aggregate(total=Sum('source_quantity_base'))['total'] or Decimal('0')
    return (to_decimal(entries) + to_decimal(produced) - to_decimal(sales) - to_decimal(consumed)).quantize(Decimal('0.001'))



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



def build_traceability_rows(participant=None, product=None):
    from .models import EntryRecord, SaleRecord, TransformationRecord

    sources = defaultdict(list)
    rows = []

    entries_qs = EntryRecord.objects.select_related('participant', 'product').order_by('movement_date', 'id')
    sales_qs = SaleRecord.objects.select_related('participant', 'product').order_by('movement_date', 'id')
    trans_qs = TransformationRecord.objects.select_related('participant', 'source_product', 'target_product').order_by('movement_date', 'id')

    if participant:
        entries_qs = entries_qs.filter(participant=participant)
        sales_qs = sales_qs.filter(participant=participant)
        trans_qs = trans_qs.filter(participant=participant)
    if product:
        entries_qs = entries_qs.filter(product=product)
        sales_qs = sales_qs.filter(product=product)
        trans_qs = trans_qs.filter(source_product=product) | trans_qs.filter(target_product=product)

    def add_source(participant_id, product_obj, ref_type, ref_id, ref_label, movement_date, quantity):
        sources[(participant_id, product_obj.id)].append(
            TraceSource(
                product_id=product_obj.id,
                participant_id=participant_id,
                ref_type=ref_type,
                ref_id=ref_id,
                ref_label=ref_label,
                movement_date=movement_date,
                quantity_total=to_decimal(quantity),
                quantity_remaining=to_decimal(quantity),
                unit_label=product_obj.get_unit_display(),
            )
        )

    def consume(participant_obj, product_obj, qty_needed, use_type, use_label, movement_date):
        qty_needed = to_decimal(qty_needed)
        bucket_key = (participant_obj.id, product_obj.id)
        for source in sources[bucket_key]:
            if qty_needed <= 0:
                break
            if source.quantity_remaining <= 0:
                continue
            consumed = min(source.quantity_remaining, qty_needed)
            source.quantity_remaining -= consumed
            qty_needed -= consumed
            rows.append({
                'participant': participant_obj,
                'product': product_obj,
                'use_type': use_type,
                'use_label': use_label,
                'use_date': movement_date,
                'source_label': source.ref_label,
                'source_date': source.movement_date,
                'quantity': consumed.quantize(Decimal('0.001')),
                'unit': product_obj.get_unit_display(),
            })
        if qty_needed > 0:
            rows.append({
                'participant': participant_obj,
                'product': product_obj,
                'use_type': use_type,
                'use_label': use_label,
                'use_date': movement_date,
                'source_label': 'Saldo sem origem suficiente',
                'source_date': movement_date,
                'quantity': qty_needed.quantize(Decimal('0.001')),
                'unit': product_obj.get_unit_display(),
            })

    # Merge all chronological events.
    events = []
    for e in entries_qs:
        events.append(('entry', e.movement_date, e.id, e))
    for t in trans_qs:
        events.append(('trans', t.movement_date, t.id, t))
    for s in sales_qs:
        events.append(('sale', s.movement_date, s.id, s))
    events.sort(key=lambda item: (item[1], item[2], item[0]))

    for kind, movement_date, _, obj in events:
        if kind == 'entry':
            add_source(obj.participant_id, obj.product, 'entry', obj.id, f'Entrada {obj.document_number}', obj.movement_date, obj.quantity_base)
        elif kind == 'trans':
            consume(obj.participant, obj.source_product, obj.source_quantity_base, 'transformação', f'Transformação #{obj.id} consumo', obj.movement_date)
            add_source(obj.participant_id, obj.target_product, 'transformation', obj.id, f'Transformação #{obj.id} produção', obj.movement_date, obj.target_quantity_base)
        elif kind == 'sale':
            consume(obj.participant, obj.product, obj.quantity_base, 'saída', f'Saída {obj.document_number}', obj.movement_date)

    return rows
