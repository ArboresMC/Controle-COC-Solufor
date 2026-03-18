from datetime import date
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from compliance.models import MonthlyClosing
from .forms import EntryRecordForm, SaleRecordForm
from .models import EntryRecord, SaleRecord

class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        month_entries = EntryRecord.objects.all()
        month_sales = SaleRecord.objects.all()
        closings = MonthlyClosing.objects.filter(year=today.year, month=today.month)
        if not user.is_manager and user.participant:
            month_entries = month_entries.filter(participant=user.participant)
            month_sales = month_sales.filter(participant=user.participant)
            closings = closings.filter(participant=user.participant)
        month_entries = month_entries.filter(movement_date__year=today.year, movement_date__month=today.month)
        month_sales = month_sales.filter(movement_date__year=today.year, movement_date__month=today.month)
        ctx['entries_count'] = month_entries.count()
        ctx['sales_count'] = month_sales.count()
        ctx['entries_total'] = month_entries.aggregate(total=Sum('quantity'))['total'] or 0
        ctx['sales_total'] = month_sales.aggregate(total=Sum('quantity'))['total'] or 0
        ctx['needs_correction'] = (month_entries.filter(status='needs_correction').count() + month_sales.filter(status='needs_correction').count())
        ctx['current_closings'] = closings
        ctx['recent_entries'] = month_entries[:5]
        ctx['recent_sales'] = month_sales[:5]
        return ctx

class ParticipantScopedMixin(LoginRequiredMixin):
    def get_queryset(self):
        qs = self.model.objects.select_related('participant', 'product')
        user = self.request.user
        if user.is_manager or user.is_auditor:
            return qs
        if user.participant:
            return qs.filter(participant=user.participant)
        return qs.none()

class EntryListView(ParticipantScopedMixin, ListView):
    model = EntryRecord
    template_name = 'transactions/entry_list.html'
    context_object_name = 'records'

class SaleListView(ParticipantScopedMixin, ListView):
    model = SaleRecord
    template_name = 'transactions/sale_list.html'
    context_object_name = 'records'

class EntryCreateView(LoginRequiredMixin, CreateView):
    model = EntryRecord
    form_class = EntryRecordForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('entry_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.request.user.participant
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.participant = self.request.user.participant
        obj.unit_snapshot = obj.product.unit
        obj.save()
        messages.success(self.request, 'Entrada salva com sucesso.')
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_manager or request.user.is_auditor or not request.user.participant:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

class EntryUpdateView(LoginRequiredMixin, UpdateView):
    model = EntryRecord
    form_class = EntryRecordForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('entry_list')

    def get_queryset(self):
        return EntryRecord.objects.filter(participant=self.request.user.participant).exclude(status='reviewed')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.request.user.participant
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.unit_snapshot = obj.product.unit
        obj.save()
        messages.success(self.request, 'Entrada atualizada com sucesso.')
        return redirect(self.success_url)

class SaleCreateView(LoginRequiredMixin, CreateView):
    model = SaleRecord
    form_class = SaleRecordForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('sale_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.request.user.participant
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.participant = self.request.user.participant
        obj.unit_snapshot = obj.product.unit
        obj.save()
        messages.success(self.request, 'Saída salva com sucesso.')
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_manager or request.user.is_auditor or not request.user.participant:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

class SaleUpdateView(LoginRequiredMixin, UpdateView):
    model = SaleRecord
    form_class = SaleRecordForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('sale_list')

    def get_queryset(self):
        return SaleRecord.objects.filter(participant=self.request.user.participant).exclude(status='reviewed')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.request.user.participant
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.unit_snapshot = obj.product.unit
        obj.save()
        messages.success(self.request, 'Saída atualizada com sucesso.')
        return redirect(self.success_url)

class ManagerReviewEntryListView(ManagerRequiredMixin, ListView):
    model = EntryRecord
    template_name = 'transactions/review_list.html'
    context_object_name = 'records'

class ManagerReviewSaleListView(ManagerRequiredMixin, ListView):
    model = SaleRecord
    template_name = 'transactions/review_list.html'
    context_object_name = 'records'
