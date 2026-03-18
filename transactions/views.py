from datetime import date
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from catalog.models import Counterparty, Product
from compliance.models import MonthlyClosing
from participants.models import Participant
from .forms import EntryRecordForm, SaleRecordForm, TransformationRecordForm
from .models import EntryRecord, SaleRecord, TransformationRecord
from .services import (
    get_available_balance,
    get_transformation_rule,
    get_balance_items,
    get_participant_balance_summary,
)


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        month_entries = EntryRecord.objects.select_related('participant', 'product')
        month_sales = SaleRecord.objects.select_related('participant', 'product')
        transformations = TransformationRecord.objects.select_related('participant', 'source_product', 'target_product')
        closings = MonthlyClosing.objects.select_related('participant').filter(year=today.year, month=today.month)

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
        ctx['needs_correction'] = month_entries.filter(status='needs_correction').count() + month_sales.filter(status='needs_correction').count()
        ctx['current_closings'] = closings
        ctx['recent_entries'] = month_entries[:5]
        ctx['recent_sales'] = month_sales[:5]
        ctx['recent_transformations'] = transformations[:5]

        if user.is_manager:
            participant_summaries = [get_participant_balance_summary(p) for p in Participant.objects.filter(status='active').order_by('trade_name', 'legal_name')[:8]]
            closings_qs = MonthlyClosing.objects.filter(year=today.year, month=today.month)
            ctx['manager_metrics'] = {
                'participants_active': Participant.objects.filter(status='active').count(),
                'participants_without_closing': Participant.objects.filter(status='active').exclude(id__in=closings_qs.values_list('participant_id', flat=True)).count(),
                'closings_submitted': closings_qs.filter(status='submitted').count(),
                'closings_rejected': closings_qs.filter(status='rejected').count(),
                'low_balance_participants': len([s for s in participant_summaries if s['low_count']]),
            }
            ctx['participant_summaries'] = participant_summaries
            ctx['participants_without_closing'] = Participant.objects.filter(status='active').exclude(id__in=closings_qs.values_list('participant_id', flat=True))[:10]
            ctx['balance_items'] = []
            ctx['projected_balance_items'] = []
        else:
            participant = getattr(user, 'participant', None)
            ctx['balance_items'] = get_balance_items(participant, projected=False) if participant else []
            ctx['projected_balance_items'] = get_balance_items(participant, projected=True) if participant else []
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

    def _resolve_product(self, form):
        payload = form.cleaned_data.get('new_product_payload')
        if payload:
            product, _ = Product.objects.get_or_create(
                name=payload['name'],
                defaults={'unit': payload['unit'], 'active': True}
            )
            return product
        return form.cleaned_data['product']

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.participant = self.request.user.participant
        obj.product = self._resolve_product(form)
        obj.movement_unit = form.cleaned_data['movement_unit']
        obj.unit_snapshot = obj.product.unit
        from .services import convert_to_base
        obj.quantity_base = convert_to_base(obj.product, obj.quantity, obj.movement_unit)
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


class EntryUpdateView(EntryCreateView, UpdateView):
    model = EntryRecord
    success_url = reverse_lazy('entry_list')

    def get_queryset(self):
        return EntryRecord.objects.filter(participant=self.request.user.participant).exclude(status='reviewed')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Entrada atualizada com sucesso.')
        return response


class SaleCreateView(LoginRequiredMixin, CreateView):
    model = SaleRecord
    form_class = SaleRecordForm
    template_name = 'transactions/form.html'
    success_url = reverse_lazy('sale_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.request.user.participant
        return kwargs

    def _resolve_product(self, form):
        payload = form.cleaned_data.get('new_product_payload')
        if payload:
            product, _ = Product.objects.get_or_create(
                name=payload['name'],
                defaults={'unit': payload['unit'], 'active': True}
            )
            return product
        return form.cleaned_data['product']

    def _resolve_customer(self, form):
        new_name = (form.cleaned_data.get('new_customer_name') or '').strip()
        if new_name:
            customer, _ = Counterparty.objects.get_or_create(
                participant=self.request.user.participant,
                name=new_name,
                defaults={'type': 'customer'}
            )
            return customer
        return form.cleaned_data['customer']

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.participant = self.request.user.participant
        obj.product = self._resolve_product(form)
        obj.customer = self._resolve_customer(form)
        obj.movement_unit = form.cleaned_data['movement_unit']
        obj.unit_snapshot = obj.product.unit
        from .services import convert_to_base
        obj.quantity_base = convert_to_base(obj.product, obj.quantity, obj.movement_unit)
        available = get_available_balance(self.request.user.participant, obj.product)
        if obj.quantity_base > available:
            form.add_error('quantity', f'Saldo insuficiente. Disponível: {available} {obj.product.get_unit_display()}. Solicitado: {obj.quantity_base} {obj.product.get_unit_display()}.')
            return self.form_invalid(form)
        obj.save()
        messages.success(self.request, 'Saída salva com sucesso.')
        return redirect(self.success_url)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_manager or request.user.is_auditor or not request.user.participant:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class SaleUpdateView(SaleCreateView, UpdateView):
    model = SaleRecord
    success_url = reverse_lazy('sale_list')

    def get_queryset(self):
        return SaleRecord.objects.filter(participant=self.request.user.participant).exclude(status='reviewed')

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.participant = self.request.user.participant
        obj.product = self._resolve_product(form)
        obj.customer = self._resolve_customer(form)
        obj.movement_unit = form.cleaned_data['movement_unit']
        obj.unit_snapshot = obj.product.unit
        from .services import convert_to_base
        obj.quantity_base = convert_to_base(obj.product, obj.quantity, obj.movement_unit)
        current_base = self.get_object().quantity_base
        available = get_available_balance(self.request.user.participant, obj.product) + current_base
        if obj.quantity_base > available:
            form.add_error('quantity', f'Saldo insuficiente. Disponível: {available} {obj.product.get_unit_display()}. Solicitado: {obj.quantity_base} {obj.product.get_unit_display()}.')
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

    def _resolve_products(self, form):
        source_product = form.cleaned_data.get('source_product')
        target_product = form.cleaned_data.get('target_product')
        source_payload = form.cleaned_data.get('new_source_product_payload')
        target_payload = form.cleaned_data.get('new_target_product_payload')
        if source_payload:
            source_product, _ = Product.objects.get_or_create(name=source_payload['name'], defaults={'unit': source_payload['unit'], 'active': True})
        if target_payload:
            base_unit = target_product.unit if target_product else (source_product.unit if source_product else 'm3')
            target_product, _ = Product.objects.get_or_create(name=target_payload['name'], defaults={'unit': base_unit, 'active': True})
        return source_product, target_product

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.created_by = self.request.user
        obj.participant = self.request.user.participant
        obj.source_product, obj.target_product = self._resolve_products(form)
        obj.source_unit = form.cleaned_data['source_unit']
        from .services import convert_to_base, calculate_target_from_source
        obj.source_quantity_base = convert_to_base(obj.source_product, obj.source_quantity, obj.source_unit)
        obj.target_quantity_base = calculate_target_from_source(obj.source_product, obj.target_product, obj.source_quantity_base)
        obj.target_unit_snapshot = obj.target_product.unit
        rule = get_transformation_rule(obj.source_product, obj.target_product)
        obj.yield_factor_snapshot = rule.yield_factor
        available = get_available_balance(self.request.user.participant, obj.source_product)
        if obj.source_quantity_base > available:
            form.add_error('source_quantity', f'Saldo insuficiente do produto origem. Disponível: {available} {obj.source_product.get_unit_display()}. Solicitado: {obj.source_quantity_base} {obj.source_product.get_unit_display()}.')
            return self.form_invalid(form)
        obj.save()
        messages.success(self.request, f'Transformação salva. Gerados {obj.target_quantity_base} {obj.target_product.get_unit_display()} de {obj.target_product}.')
        return redirect(self.success_url)


class TransformationUpdateView(TransformationCreateView, UpdateView):
    model = TransformationRecord
    success_url = reverse_lazy('transformation_list')

    def get_queryset(self):
        return TransformationRecord.objects.filter(participant=self.request.user.participant)

    def form_valid(self, form):
        obj = form.save(commit=False)
        old = self.get_object()
        obj.source_product, obj.target_product = self._resolve_products(form)
        obj.source_unit = form.cleaned_data['source_unit']
        from .services import convert_to_base, calculate_target_from_source
        obj.source_quantity_base = convert_to_base(obj.source_product, obj.source_quantity, obj.source_unit)
        obj.target_quantity_base = calculate_target_from_source(obj.source_product, obj.target_product, obj.source_quantity_base)
        obj.target_unit_snapshot = obj.target_product.unit
        rule = get_transformation_rule(obj.source_product, obj.target_product)
        obj.yield_factor_snapshot = rule.yield_factor
        available = get_available_balance(self.request.user.participant, obj.source_product) + old.source_quantity_base
        if obj.source_quantity_base > available:
            form.add_error('source_quantity', f'Saldo insuficiente do produto origem. Disponível: {available} {obj.source_product.get_unit_display()}. Solicitado: {obj.source_quantity_base} {obj.source_product.get_unit_display()}.')
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
