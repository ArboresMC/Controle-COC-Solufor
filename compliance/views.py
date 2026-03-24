from datetime import date
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import FormView, ListView
from .forms import MonthlyClosingForm
from .models import MonthlyClosing

class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager

class ClosingListView(LoginRequiredMixin, ListView):
    model = MonthlyClosing; template_name = 'compliance/closing_list.html'; context_object_name = 'closings'
    def get_queryset(self):
        qs = MonthlyClosing.objects.select_related('participant', 'reviewed_by'); user = self.request.user; org = getattr(user, 'current_organization', None)
        if user.is_manager or user.is_auditor: return qs.filter(participant__organization=org) if org else qs.none()
        if user.participant: return qs.filter(participant=user.participant)
        return qs.none()

class SubmitCurrentClosingView(LoginRequiredMixin, FormView):
    template_name = 'compliance/submit_closing.html'; form_class = MonthlyClosingForm
    def get_closing(self):
        today = date.today()
        return MonthlyClosing.objects.get_or_create(participant=self.request.user.participant, year=today.year, month=today.month, defaults={'status': 'open'})[0]
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); ctx['closing'] = self.get_closing(); return ctx
    def form_valid(self, form):
        closing = self.get_closing()
        if closing.status == 'approved': messages.error(self.request, 'Este fechamento já foi aprovado e não pode ser reenviado.'); return redirect('closing_list')
        closing.participant_notes = form.cleaned_data['participant_notes']; closing.declaration_no_movement = form.cleaned_data['declaration_no_movement']; closing.status = 'submitted'; closing.submitted_at = timezone.now(); closing.save(); messages.success(self.request, 'Fechamento enviado com sucesso.'); return redirect('closing_list')

class ManagerClosingListView(ManagerRequiredMixin, ListView):
    model = MonthlyClosing; template_name = 'compliance/manager_closing_list.html'; context_object_name = 'closings'
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return MonthlyClosing.objects.select_related('participant', 'reviewed_by').filter(participant__organization=org) if org else MonthlyClosing.objects.none()

class ManagerClosingApproveView(ManagerRequiredMixin, ListView):
    model = MonthlyClosing; template_name = 'compliance/manager_closing_list.html'
    def get(self, request, *args, **kwargs):
        org = getattr(request.user, 'current_organization', None)
        closing = get_object_or_404(MonthlyClosing.objects.filter(participant__organization=org), pk=kwargs['pk'])
        closing.status = 'approved'; closing.reviewed_at = timezone.now(); closing.reviewed_by = request.user; closing.save(); messages.success(request, 'Fechamento aprovado.'); return redirect('manager_closing_list')

class ManagerClosingRejectView(ManagerRequiredMixin, ListView):
    model = MonthlyClosing; template_name = 'compliance/manager_closing_list.html'
    def get(self, request, *args, **kwargs):
        org = getattr(request.user, 'current_organization', None)
        closing = get_object_or_404(MonthlyClosing.objects.filter(participant__organization=org), pk=kwargs['pk'])
        closing.status = 'rejected'; closing.reviewed_at = timezone.now(); closing.reviewed_by = request.user; closing.save(); messages.success(request, 'Fechamento rejeitado.'); return redirect('manager_closing_list')
