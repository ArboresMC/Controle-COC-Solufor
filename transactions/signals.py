from decimal import Decimal

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from compliance.models import MonthlyClosing

from .models import EntryRecord, LotAllocation, SaleRecord, TraceLot, TransformationRecord
from .performance import invalidate_for_participant


def _to_decimal(value):
    if value is None:
        return Decimal('0')
    return Decimal(str(value))


def _refresh_lot_quantity_available(lot):
    total_allocated = _to_decimal(lot.allocations.aggregate(total=models.Sum('quantity_base'))['total'])
    lot.quantity_available = (_to_decimal(lot.quantity_base) - total_allocated).quantize(Decimal('0.001'))
    TraceLot.objects.filter(pk=lot.pk).update(quantity_available=lot.quantity_available)


from django.db import models  # noqa: E402


@receiver(pre_save, sender=LotAllocation)
def remember_previous_allocation(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_quantity_base = None
        return
    previous = sender.objects.filter(pk=instance.pk).values('quantity_base').first()
    instance._previous_quantity_base = _to_decimal(previous['quantity_base']) if previous else None


@receiver(post_save, sender=LotAllocation)
def update_lot_balance_after_save(sender, instance, created, **kwargs):
    lot = instance.lot
    current_qty = _to_decimal(instance.quantity_base)
    previous_qty = _to_decimal(getattr(instance, '_previous_quantity_base', Decimal('0')))
    delta = current_qty if created else current_qty - previous_qty
    TraceLot.objects.filter(pk=lot.pk).update(quantity_available=models.F('quantity_available') - delta)
    org_id = getattr(instance.participant.organization, 'id', None) if instance.participant_id else None
    invalidate_for_participant(instance.participant_id, org_id)


@receiver(post_delete, sender=LotAllocation)
def update_lot_balance_after_delete(sender, instance, **kwargs):
    TraceLot.objects.filter(pk=instance.lot_id).update(quantity_available=models.F('quantity_available') + _to_decimal(instance.quantity_base))
    org_id = getattr(instance.participant.organization, 'id', None) if instance.participant_id else None
    invalidate_for_participant(instance.participant_id, org_id)


def _invalidate_transaction_scope(instance):
    participant = getattr(instance, 'participant', None)
    participant_id = getattr(participant, 'id', None) or getattr(instance, 'participant_id', None)
    organization_id = getattr(getattr(participant, 'organization', None), 'id', None)
    invalidate_for_participant(participant_id, organization_id)


@receiver(post_save, sender=EntryRecord)
@receiver(post_delete, sender=EntryRecord)
@receiver(post_save, sender=SaleRecord)
@receiver(post_delete, sender=SaleRecord)
@receiver(post_save, sender=TransformationRecord)
@receiver(post_delete, sender=TransformationRecord)
def invalidate_transaction_cache(sender, instance, **kwargs):
    _invalidate_transaction_scope(instance)


@receiver(post_save, sender=TraceLot)
@receiver(post_delete, sender=TraceLot)
def invalidate_lot_cache(sender, instance, **kwargs):
    _invalidate_transaction_scope(instance)


@receiver(post_save, sender=MonthlyClosing)
@receiver(post_delete, sender=MonthlyClosing)
def invalidate_closing_cache(sender, instance, **kwargs):
    _invalidate_transaction_scope(instance)
