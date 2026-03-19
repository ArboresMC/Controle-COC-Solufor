
from django.db import models
from participants.models import Participant

class ProductTransformationRule(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='transformation_rules',
        verbose_name='Participante',
        null=True,
        blank=True
    )
    source_product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='transformation_rules_out')
    target_product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='transformation_rules_in')
    yield_factor = models.DecimalField(max_digits=14, decimal_places=6)
    notes = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('participant', 'source_product', 'target_product')
