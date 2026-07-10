from datetime import date


def pendencias(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'pendencias_count': 0}
    try:
        from .models import EntryRecord, SaleRecord
        from compliance.models import MonthlyClosing
        count = 0
        if user.is_manager:
            org = getattr(user, 'current_organization', None)
            if org:
                count += MonthlyClosing.objects.filter(participant__organization=org, status='submitted').count()
                count += EntryRecord.objects.filter(participant__organization=org, status='needs_correction').count()
                count += SaleRecord.objects.filter(participant__organization=org, status='needs_correction').count()
        elif hasattr(user, 'participant') and user.participant:
            participant = user.participant
            count += EntryRecord.objects.filter(participant=participant, status='needs_correction').count()
            count += SaleRecord.objects.filter(participant=participant, status='needs_correction').count()
        return {'pendencias_count': count}
    except Exception:
        return {'pendencias_count': 0}
