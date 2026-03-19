
def get_transformation_rule(participant, source_product, target_product):
    from catalog.models import ProductTransformationRule
    return ProductTransformationRule.objects.filter(
        participant=participant,
        source_product=source_product,
        target_product=target_product,
        active=True
    ).first()
