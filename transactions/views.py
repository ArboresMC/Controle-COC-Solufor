from datetime import date
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from catalog.models import Counterparty, Product
from compliance.models import MonthlyClosing
from .forms import EntryRecordForm, SaleRecordForm, TransformationRecordForm
from .models import EntryRecord, SaleRecord, TransformationRecord
from .services import get_available_balance, get_transformation_rule


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
        transformations = TransformationRecord.objects.all()
        closings = MonthlyClosing.objects.filter(year=today.year, month=today.month)
        if not user.is_manager and getattr(user, 'participant', None):
            month_entries = month_entries.filter(participant=user.participant)
            month_sales = month_sales.filter(participant=user.participant)
            transformations = transformations.filter(participant=user.participant)
            closings = closings.filter(participant=user.participant)
        elif not user.is_manager:
            month_entries = EntryRecord.objects.none()
            month_sales = SaleRecord.objects.none()
            transformations = TransformationRecord.objects.none()
            closings = MonthlyClosing.objects.none()
        month_entries = month_entries.filter(movement_date__year=today.year, movement_date__month=today.month)
        month_sales = month_sales.filter(movement_date__year=today.year, movement_date__month=today.month)
        transformations = transformations.filter(movement_date__year=today.year, movement_date__month=today.month)
        ctx['entries_count'] = month_entries.count()
        ctx['sales_count'] = month_sales.count()
        ctx['transformations_count'] = transformations.count()
        ctx['entries_total'] = month_entries.aggregate(total=Sum('quantity_base'))['total'] or 0
        ctx['sales_total'] = month_sales.aggregate(total=Sum('quantity_base'))['total'] or 0
        ctx['needs_correction'] = (month_entries.filter(status='needs_correction').count() + month_sales.filter(status='needs_correction').count())
        ctx['current_closings'] = closings
        ctx['recent_entries'] = month_entries[:5]
        ctx['recent_sales'] = month_sales[:5]
        ctx['recent_transformations'] = transformations[:5]
        balance_items = []
        if user.is_manager:
            products = Product.objects.filter(active=True).order_by('name')[:10]
            participant = None
        else:
            participant = getattr(user, 'participant', None)
            products = Product.objects.filter(active=True).order_by('name')
        if participant:
            for product in products:
                balance = get_available_balance(participant, product)
                if balance != 0:
                    balance_items.append({'product': product, 'balance': balance, 'unit': product.get_unit_display()})
        ctx['balance_items'] = balance_items
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


class TransformationListView(LoginRequiredMixin, ListView):
    model = TransformationRecord
    template_name = 'transactions/transformation_list.html'
    context_object_name = 'records'

    def get_queryset(self):
        qs = TransformationRecord.objects.select_related('participant', 'source_product', 'target_product')
        user = self.request.user
        if user.is_manager or user.is_auditor:
            return qs
        if user.participant:
            return qs.filter(participant=user.participant)
        return qs.none()


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
        obj.movement_unit = form.cleaned_data['movement_unit']
        obj.unit_snapshot = obj.product.unit
        obj.quantity_base = form.cleaned_data['quantity_base']
        supplier, _ = Counterparty.objects.get_or_create(
            participant=self.request.user.participant,
            name='Não informado',
            defaults={'type': 'supplier'}
        )
        obj.supplier = supplier
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
        obj.movement_unit = form.cleaned_data['movement_unit']
        obj.unit_snapshot = obj.product.unit
        obj.quantity_base = form.cleaned_data['quantity_base']
        supplier, _ = Counterparty.objects.get_or_create(
            participant=self.request.user.participant,
            name='Não informado',
            defaults={'type': 'supplier'}
        )
        obj.supplier = supplier
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
        obj.movement_unit = form.cleaned_data['movement_unit']
        obj.unit_snapshot = obj.product.unit
        obj.quantity_base = form.cleaned_data['quantity_base']
        available = get_available_balance(self.request.user.participant, obj.product)
        if obj.quantity_base > available:
            form.add_error('quantity', f'Saldo insuficiente. Disponível: {available} {obj.product.get_unit_display()}.')
            return self.form_invalid(form)
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
        obj.movement_unit = form.cleaned_data['movement_unit']
        obj.unit_snapshot = obj.product.unit
        obj.quantity_base = form.cleaned_data['quantity_base']
        current_base = self.get_object().quantity_base
        available = get_available_balance(self.request.user.participant, obj.product) + current_base
        if obj.quantity_base > available:
            form.add_error('quantity', f'Saldo insuficiente. Disponível: {available} {obj.product.get_unit_display()}.')
            return self.form_invalid(form)
        obj.save()
        messages.success(self.request, 'Saída atualizada com sucesso.')
        return redirect(self.success_url)


class TransformationCreateView(LoginRequiredMixin, CreateView):
    model = TransformationRecord
    form_class = TransformationRecordForm
    template_name = 'transactions/transformation_form.html'
    success_url = reverse_lazy('transformation_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.request.user.participant
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_manager or request.user.is_auditor or not request.user.participant:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.participant = self.request.user.participant
        obj.source_unit = form.cleaned_data['source_unit']
        obj.source_quantity_base = form.cleaned_data['source_quantity_base']
        obj.target_quantity_base = form.cleaned_data['target_quantity_base']
        obj.target_unit_snapshot = obj.target_product.unit
        rule = get_transformation_rule(obj.source_product, obj.target_product)
        obj.yield_factor_snapshot = rule.yield_factor
        available = get_available_balance(self.request.user.participant, obj.source_product)
        if obj.source_quantity_base > available:
            form.add_error('source_quantity', f'Saldo insuficiente do produto origem. Disponível: {available} {obj.source_product.get_unit_display()}.')
            return self.form_invalid(form)
        obj.save()
        messages.success(self.request, f'Transformação salva. Gerados {obj.target_quantity_base} {obj.target_product.get_unit_display()} de {obj.target_product}.')
        return redirect(self.success_url)


class TransformationUpdateView(LoginRequiredMixin, UpdateView):
    model = TransformationRecord
    form_class = TransformationRecordForm
    template_name = 'transactions/transformation_form.html'
    success_url = reverse_lazy('transformation_list')

    def get_queryset(self):
        return TransformationRecord.objects.filter(participant=self.request.user.participant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.request.user.participant
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        old = self.get_object()
        obj.source_unit = form.cleaned_data['source_unit']
        obj.source_quantity_base = form.cleaned_data['source_quantity_base']
        obj.target_quantity_base = form.cleaned_data['target_quantity_base']
        obj.target_unit_snapshot = obj.target_product.unit
        rule = get_transformation_rule(obj.source_product, obj.target_product)
        obj.yield_factor_snapshot = rule.yield_factor
        available = get_available_balance(self.request.user.participant, obj.source_product) + old.source_quantity_base
        if obj.source_quantity_base > available:
            form.add_error('source_quantity', f'Saldo insuficiente do produto origem. Disponível: {available} {obj.source_product.get_unit_display()}.')
            return self.form_invalid(form)
        obj.save()
        messages.success(self.request, 'Transformação atualizada com sucesso.')
        return redirect(self.success_url)


class ManagerReviewEntryListView(ManagerRequiredMixin, ListView):
    model = EntryRecord
    template_name = 'transactions/review_list.html'
    context_object_name = 'records'


class ManagerReviewSaleListView(ManagerRequiredMixin, ListView):
    model = SaleRecord
    template_name = 'transactions/review_list.html'
    context_object_name = 'records'
