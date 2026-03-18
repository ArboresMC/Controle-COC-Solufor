from decimal import Decimal
from django.db.models import Sum
from catalog.models import ProductUnitConversion, ProductTransformationRule


def to_decimal(value):
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def get_unit_conversion_factor(product, from_unit: str) -> Decimal:
    from catalog.models import Product
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



def get_available_balance(participant, product):
    from .models import EntryRecord, SaleRecord, TransformationRecord

    entries = EntryRecord.objects.filter(participant=participant, product=product).aggregate(total=Sum('quantity_base'))['total'] or Decimal('0')
    sales = SaleRecord.objects.filter(participant=participant, product=product).aggregate(total=Sum('quantity_base'))['total'] or Decimal('0')
    produced = TransformationRecord.objects.filter(participant=participant, target_product=product).aggregate(total=Sum('target_quantity_base'))['total'] or Decimal('0')
    consumed = TransformationRecord.objects.filter(participant=participant, source_product=product).aggregate(total=Sum('source_quantity_base'))['total'] or Decimal('0')
    return (to_decimal(entries) + to_decimal(produced) - to_decimal(sales) - to_decimal(consumed)).quantize(Decimal('0.001'))
