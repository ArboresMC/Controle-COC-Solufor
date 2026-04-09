import calendar
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from .models import MonthlyClosing
from participants.models import Participant
from transactions.models import EntryRecord, SaleRecord, TransformationRecord


class ManagerRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and
                (request.user.is_manager or request.user.is_auditor or request.user.is_superuser)):
            messages.error(request, 'Acesso restrito.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class ParticipantRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not hasattr(request.user, 'participant') or request.user.participant is None:
            messages.error(request, 'Seu usuário não está vinculado a um participante.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class MyClosingsView(ParticipantRequiredMixin, ListView):
    template_name = 'compliance/my_closings.html'
    context_object_name = 'closings'

    def get_queryset(self):
        return MonthlyClosing.objects.filter(
            participant=self.request.user.participant
        ).order_by('-year', '-month')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now()
        ctx['current_year'] = today.year
        ctx['months'] = [
            (i, calendar.month_name[i].capitalize())
            for i in range(1, 13)
        ]
        return ctx


class SubmitClosingView(ParticipantRequiredMixin, View):
    def post(self, request, pk):
        closing = get_object_or_404(
            MonthlyClosing,
            pk=pk,
            participant=request.user.participant,
        )
        if not closing.is_editable:
            messages.error(request, 'Este fechamento não pode ser enviado no status atual.')
            return redirect('my_closings')

        closing.status = MonthlyClosing.STATUS_SUBMITTED
        closing.submitted_at = timezone.now()
        closing.rejection_reason = None
        closing.save()

        messages.success(
            request,
            f'Fechamento de {closing.period_display} enviado para aprovação do gestor.'
        )
        return redirect('my_closings')


class CreateClosingView(ParticipantRequiredMixin, View):
    def post(self, request):
        participant = request.user.participant
        year = int(request.POST.get('year'))
        month = int(request.POST.get('month'))

        closing, created = MonthlyClosing.objects.get_or_create(
            participant=participant,
            year=year,
            month=month,
        )
        if not created and closing.is_locked:
            messages.warning(request, 'Este período já está aprovado e não pode ser reaberto.')
        elif not created:
            messages.info(request, f'Fechamento de {closing.period_display} já existe.')

        return redirect('my_closings')


class ManagerClosingDashboardView(ManagerRequiredMixin, TemplateView):
    template_name = 'compliance/manager_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['submitted_closings'] = (
            MonthlyClosing.objects
            .filter(status=MonthlyClosing.STATUS_SUBMITTED)
            .select_related('participant')
            .order_by('submitted_at')
        )
        ctx['recent_closings'] = (
            MonthlyClosing.objects
            .filter(status__in=[MonthlyClosing.STATUS_APPROVED, MonthlyClosing.STATUS_REJECTED])
            .select_related('participant', 'reviewed_by')
            .order_by('-reviewed_at')[:20]
        )
        return ctx


class ClosingDetailView(ManagerRequiredMixin, TemplateView):
    template_name = 'compliance/closing_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        closing = get_object_or_404(MonthlyClosing, pk=self.kwargs['pk'])
        ctx['closing'] = closing

        ctx['entries'] = EntryRecord.objects.filter(
            participant=closing.participant,
            movement_date__year=closing.year,
            movement_date__month=closing.month,
        ).order_by('movement_date')

        ctx['sales'] = SaleRecord.objects.filter(
            participant=closing.participant,
            movement_date__year=closing.year,
            movement_date__month=closing.month,
        ).order_by('movement_date')

        ctx['transformations'] = TransformationRecord.objects.filter(
            participant=closing.participant,
            movement_date__year=closing.year,
            movement_date__month=closing.month,
        ).order_by('movement_date')

        return ctx


class ApproveClosingView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        closing = get_object_or_404(MonthlyClosing, pk=pk)

        if closing.status != MonthlyClosing.STATUS_SUBMITTED:
            messages.error(request, 'Somente fechamentos "Aguardando aprovação" podem ser aprovados.')
            return redirect('manager_closing_dashboard')

        closing.status = MonthlyClosing.STATUS_APPROVED
        closing.reviewed_at = timezone.now()
        closing.reviewed_by = request.user
        closing.rejection_reason = None
        closing.save()

        messages.success(
            request,
            f'Fechamento de {closing.period_display} ({closing.participant}) aprovado com sucesso.'
        )
        return redirect('manager_closing_dashboard')


class RejectClosingView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        closing = get_object_or_404(MonthlyClosing, pk=pk)

        if closing.status != MonthlyClosing.STATUS_SUBMITTED:
            messages.error(request, 'Somente fechamentos "Aguardando aprovação" podem ser rejeitados.')
            return redirect('manager_closing_dashboard')

        reason = request.POST.get('rejection_reason', '').strip()
        if not reason:
            messages.error(request, 'É obrigatório informar o motivo da rejeição.')
            return redirect('closing_detail', pk=pk)

        closing.status = MonthlyClosing.STATUS_REJECTED
        closing.reviewed_at = timezone.now()
        closing.reviewed_by = request.user
        closing.rejection_reason = reason
        closing.save()

        messages.warning(
            request,
            f'Fechamento de {closing.period_display} ({closing.participant}) rejeitado.'
        )
        return redirect('manager_closing_dashboard')
