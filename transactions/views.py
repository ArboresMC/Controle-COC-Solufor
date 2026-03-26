from datetime import date
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models, transaction
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from catalog.models import Counterparty, Product
from compliance.models import MonthlyClosing
from participants.models import Participant
from .forms import EntryRecordForm, SaleRecordForm, TransformationRecordForm
from .models import EntryRecord, SaleRecord, TransformationRecord
from .services import convert_to_base, get_available_balance, get_balance_items, get_manager_alerts, get_participant_alerts, get_participant_balance_summary, reallocate_sale, reallocate_transformation_sources, sync_entry_lot, sync_transformation_metadata, sync_transformation_target_lot


class PaginationMixin:
    paginate_by = 50


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        current_org = getattr(user, 'current_organization', None)

        month_entries = EntryRecord.objects.all()
        month_sales = SaleRecord.objects.all()
        month_transformations = TransformationRecord.objects.all()
        closings = MonthlyClosing.objects.select_related('participant').filter(year=today.year, month=today.month)

        if user.is_manager or user.is_auditor:
            if current_org:
                month_entries = month_entries.filter(participant__organization=current_org)
                month_sales = month_sales.filter(participant__organization=current_org)
                month_transformations = month_transformations.filter(participant__organization=current_org)
                closings = closings.filter(participant__organization=current_org)
            else:
                month_entries = EntryRecord.objects.none()
                month_sales = SaleRecord.objects.none()
                month_transformations = TransformationRecord.objects.none()
                closings = MonthlyClosing.objects.none()
        elif getattr(user, 'participant', None):
            month_entries = month_entries.filter(participant=user.participant)
            month_sales = month_sales.filter(participant=user.participant)
            month_transformations = month_transformations.filter(participant=user.participant)
            closings = closings.filter(participant=user.participant)
        else:
            month_entries = EntryRecord.objects.none()
            month_sales = SaleRecord.objects.none()
            month_transformations = TransformationRecord.objects.none()
            closings = MonthlyClosing.objects.none()

        month_entries = month_entries.filter(movement_date__year=today.year, movement_date__month=today.month)
        month_sales = month_sales.filter(movement_date__year=today.year, movement_date__month=today.month)
        month_transformations = month_transformations.filter(movement_date__year=today.year, movement_date__month=today.month)

        entry_summary = month_entries.aggregate(total=Sum('quantity_base'), needs=Count('id', filter=models.Q(status='needs_correction')))
        sale_summary = month_sales.aggregate(total=Sum('quantity_base'), needs=Count('id', filter=models.Q(status='needs_correction')))

        ctx['entries_count'] = month_entries.count()
        ctx['sales_count'] = month_sales.count()
        ctx['transformations_count'] = month_transformations.count()
        ctx['entries_total'] = entry_summary['total'] or 0
        ctx['sales_total'] = sale_summary['total'] or 0
        ctx['needs_correction'] = (entry_summary['needs'] or 0) + (sale_summary['needs'] or 0)
        ctx['current_closings'] = closings
        ctx['recent_entries'] = month_entries.select_related('participant', 'product')[:5]
        ctx['recent_sales'] = month_sales.select_related('participant', 'product')[:5]
        ctx['recent_transformations'] = month_transformations.select_related('participant', 'source_product', 'target_product', 'customer', 'supplier')[:5]

        if user.is_manager:
            active_participants = Participant.objects.filter(status='active')
            active_participants = active_participants.filter(organization=current_org) if current_org else Participant.objects.none()
            closings_qs = MonthlyClosing.objects.filter(year=today.year, month=today.month)
            closings_qs = closings_qs.filter(participant__organization=current_org) if current_org else MonthlyClosing.objects.none()
            participant_summaries = [
                get_participant_balance_summary(participant)
                for participant in active_participants.order_by('trade_name', 'legal_name')[:8]
            ]
            participants_without_closing = active_participants.exclude(
                id__in=closings_qs.values_list('participant_id', flat=True)
            )
            ctx['manager_metrics'] = {
                'participants_active': active_participants.count(),
                'participants_without_closing': participants_without_closing.count(),
                'closings_submitted': closings_qs.filter(status='submitted').count(),
                'closings_rejected': closings_qs.filter(status='rejected').count(),
                'low_balance_participants': len([s for s in participant_summaries if s['low_count']]),
            }
            ctx['participant_summaries'] = participant_summaries
            ctx['participants_without_closing'] = participants_without_closing[:10]
            ctx['balance_items'] = []
            ctx['projected_balance_items'] = []
            ctx['dashboard_alerts'] = get_manager_alerts(today=today, organization=current_org)
        else:
            participant = getattr(user, 'participant', None)
            ctx['balance_items'] = get_balance_items(participant, projected=False) if participant else []
            ctx['projected_balance_items'] = get_balance_items(participant, projected=True) if participant else []
            ctx['dashboard_alerts'] = get_participant_alerts(participant, today=today) if participant else []
        return ctx

class ParticipantScopedMixin(PaginationMixin, LoginRequiredMixin):
    def get_queryset(self):
        qs = self.model.objects.select_related('participant', 'product')
        user = self.request.user
        current_org = getattr(user, 'current_organization', None)
        if user.is_manager or user.is_auditor:
            return qs.filter(participant__organization=current_org) if current_org else qs.none()
        if user.participant: return qs.filter(participant=user.participant)
        return qs.none()

class DocumentCenterView(LoginRequiredMixin, TemplateView):
    DOCS_PER_SECTION = 25
    template_name = 'transactions/document_center.html'

    def _filter_docs(self, qs):
        return qs.filter(attachment__isnull=False).exclude(attachment='')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        current_org = getattr(user, 'current_organization', None)

        entry_qs = EntryRecord.objects.select_related('participant', 'product', 'supplier')
        sale_qs = SaleRecord.objects.select_related('participant', 'product', 'customer')
        transformation_qs = TransformationRecord.objects.select_related('participant', 'source_product', 'target_product', 'customer', 'supplier')

        if user.is_manager or user.is_auditor:
            if current_org:
                entry_qs = entry_qs.filter(participant__organization=current_org)
                sale_qs = sale_qs.filter(participant__organization=current_org)
                transformation_qs = transformation_qs.filter(participant__organization=current_org)
            else:
                entry_qs = EntryRecord.objects.none()
                sale_qs = SaleRecord.objects.none()
                transformation_qs = TransformationRecord.objects.none()
        elif getattr(user, 'participant', None):
            entry_qs = entry_qs.filter(participant=user.participant)
            sale_qs = sale_qs.filter(participant=user.participant)
            transformation_qs = transformation_qs.filter(participant=user.participant)
        else:
            entry_qs = EntryRecord.objects.none()
            sale_qs = SaleRecord.objects.none()
            transformation_qs = TransformationRecord.objects.none()

        entry_docs = Paginator(self._filter_docs(entry_qs).order_by('-movement_date', '-id'), self.DOCS_PER_SECTION).get_page(self.request.GET.get('entry_page'))
        sale_docs = Paginator(self._filter_docs(sale_qs).order_by('-movement_date', '-id'), self.DOCS_PER_SECTION).get_page(self.request.GET.get('sale_page'))
        transformation_docs = Paginator(self._filter_docs(transformation_qs).order_by('-movement_date', '-id'), self.DOCS_PER_SECTION).get_page(self.request.GET.get('transformation_page'))

        ctx['entry_docs'] = entry_docs
        ctx['sale_docs'] = sale_docs
        ctx['transformation_docs'] = transformation_docs
        return ctx

class EntryListView(ParticipantScopedMixin, ListView):
    model = EntryRecord; template_name = 'transactions/entry_list.html'; context_object_name = 'records'

class SaleListView(ParticipantScopedMixin, ListView):
    model = SaleRecord; template_name = 'transactions/sale_list.html'; context_object_name = 'records'

class TransformationListView(PaginationMixin, LoginRequiredMixin, ListView):
    model = TransformationRecord; template_name = 'transactions/transformation_list.html'; context_object_name = 'records'
    def get_queryset(self):
        qs = TransformationRecord.objects.select_related('participant', 'source_product', 'target_product', 'customer', 'supplier')
        user = self.request.user; current_org = getattr(user, 'current_organization', None)
        if user.is_manager or user.is_auditor: return qs.filter(participant__organization=current_org) if current_org else qs.none()
        if user.participant: return qs.filter(participant=user.participant)
        return qs.none()

class EntryCreateView(LoginRequiredMixin, CreateView):
    model = EntryRecord; form_class = EntryRecordForm; template_name = 'transactions/form.html'; success_url = reverse_lazy('entry_list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs(); kwargs['participant'] = self.request.user.participant; return kwargs
    def _resolve_product(self, form):
        payload = form.cleaned_data.get('new_product_payload')
        if payload:
            product, _ = Product.objects.get_or_create(name=payload['name'], defaults={'unit': payload['unit'], 'active': True}); return product
        return form.cleaned_data['product']
    def form_valid(self, form):
        obj = form.save(commit=False); obj.created_by = self.request.user; obj.participant = self.request.user.participant; obj.product = self._resolve_product(form); obj.movement_unit = form.cleaned_data['movement_unit']; obj.unit_snapshot = obj.product.unit; obj.quantity_base = convert_to_base(obj.product, obj.quantity, obj.movement_unit); obj.fsc_claim = form.cleaned_data.get('fsc_claim_name') or ''; obj.supplier = form.cleaned_data.get('supplier')
        if not obj.supplier_id:
            supplier, _ = Counterparty.objects.get_or_create(participant=self.request.user.participant, name='Não informado', defaults={'type': 'supplier'}); obj.supplier = supplier
        try:
            with transaction.atomic(): obj.save(); sync_entry_lot(obj)
        except Exception as exc:
            form.add_error(None, str(exc)); return self.form_invalid(form)
        messages.success(self.request, 'Entrada salva com sucesso.'); return redirect(self.success_url)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_manager or request.user.is_auditor or not request.user.participant: return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

class EntryUpdateView(EntryCreateView, UpdateView):
    model = EntryRecord; success_url = reverse_lazy('entry_list')
    def get_queryset(self): return EntryRecord.objects.filter(participant=self.request.user.participant).exclude(status='reviewed')
    def form_valid(self, form):
        obj = form.save(commit=False); obj.created_by = self.request.user; obj.participant = self.request.user.participant; obj.product = self._resolve_product(form); obj.movement_unit = form.cleaned_data['movement_unit']; obj.unit_snapshot = obj.product.unit; obj.quantity_base = convert_to_base(obj.product, obj.quantity, obj.movement_unit); obj.fsc_claim = form.cleaned_data.get('fsc_claim_name') or ''; obj.supplier = form.cleaned_data.get('supplier')
        if not obj.supplier_id:
            supplier, _ = Counterparty.objects.get_or_create(participant=self.request.user.participant, name='Não informado', defaults={'type': 'supplier'}); obj.supplier = supplier
        try:
            with transaction.atomic(): obj.save(); sync_entry_lot(obj)
        except Exception as exc:
            form.add_error(None, str(exc)); return self.form_invalid(form)
        messages.success(self.request, 'Entrada atualizada com sucesso.'); return redirect(self.success_url)

class SaleCreateView(LoginRequiredMixin, CreateView):
    model = SaleRecord; form_class = SaleRecordForm; template_name = 'transactions/form.html'; success_url = reverse_lazy('sale_list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs(); kwargs['participant'] = self.request.user.participant; return kwargs
    def _resolve_product(self, form):
        payload = form.cleaned_data.get('new_product_payload')
        if payload:
            product, _ = Product.objects.get_or_create(name=payload['name'], defaults={'unit': payload['unit'], 'active': True}); return product
        return form.cleaned_data['product']
    def _resolve_customer(self, form):
        new_name = (form.cleaned_data.get('new_customer_name') or '').strip()
        if new_name:
            customer, _ = Counterparty.objects.get_or_create(participant=self.request.user.participant, name=new_name, defaults={'type': 'customer'}); return customer
        return form.cleaned_data['customer']
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); form = ctx.get('form'); ctx['available_lots'] = getattr(form, 'available_lot_choices', []) if form else []; return ctx
    def form_valid(self, form):
        obj = form.save(commit=False); obj.created_by = self.request.user; obj.participant = self.request.user.participant; obj.product = self._resolve_product(form); obj.customer = self._resolve_customer(form); obj.movement_unit = form.cleaned_data['movement_unit']; obj.unit_snapshot = obj.product.unit; obj.quantity_base = convert_to_base(obj.product, obj.quantity, obj.movement_unit)
        available = get_available_balance(self.request.user.participant, obj.product)
        if obj.quantity_base > available:
            form.add_error('quantity', f'Saldo insuficiente. Disponível: {available} {obj.product.get_unit_display()}. Solicitado: {obj.quantity_base} {obj.product.get_unit_display()}.'); return self.form_invalid(form)
        preferred_lot = form.cleaned_data.get('source_lot'); obj.supplier = None; obj.fsc_claim = ''
        try:
            with transaction.atomic(): obj.save(); reallocate_sale(obj, preferred_lot=preferred_lot)
        except Exception as exc:
            form.add_error('source_lot', str(exc)); return self.form_invalid(form)
        messages.success(self.request, 'Saída salva com sucesso.'); return redirect(self.success_url)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_manager or request.user.is_auditor or not request.user.participant: return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

class SaleUpdateView(SaleCreateView, UpdateView):
    model = SaleRecord; success_url = reverse_lazy('sale_list')
    def get_queryset(self): return SaleRecord.objects.filter(participant=self.request.user.participant).exclude(status='reviewed')
    def form_valid(self, form):
        obj = form.save(commit=False); obj.created_by = self.request.user; obj.participant = self.request.user.participant; obj.product = self._resolve_product(form); obj.customer = self._resolve_customer(form); obj.movement_unit = form.cleaned_data['movement_unit']; obj.unit_snapshot = obj.product.unit; obj.quantity_base = convert_to_base(obj.product, obj.quantity, obj.movement_unit); current_base = self.get_object().quantity_base; available = get_available_balance(self.request.user.participant, obj.product) + current_base
        if obj.quantity_base > available:
            form.add_error('quantity', f'Saldo insuficiente. Disponível: {available} {obj.product.get_unit_display()}. Solicitado: {obj.quantity_base} {obj.product.get_unit_display()}.'); return self.form_invalid(form)
        preferred_lot = form.cleaned_data.get('source_lot'); obj.supplier = None; obj.fsc_claim = ''
        try:
            with transaction.atomic(): obj.save(); reallocate_sale(obj, preferred_lot=preferred_lot)
        except Exception as exc:
            form.add_error('source_lot', str(exc)); return self.form_invalid(form)
        messages.success(self.request, 'Saída atualizada com sucesso.'); return redirect(self.success_url)

class TransformationCreateView(LoginRequiredMixin, CreateView):
    model = TransformationRecord; form_class = TransformationRecordForm; template_name = 'transactions/transformation_form.html'; success_url = reverse_lazy('transformation_list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs(); kwargs['participant'] = self.request.user.participant; return kwargs
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs); form = ctx.get('form'); ctx['available_lots'] = getattr(form, 'available_lot_choices', []) if form else []; return ctx
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_manager or request.user.is_auditor or not request.user.participant: return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    def _resolve_products(self, form):
        source_lot = form.cleaned_data.get('source_lot'); source_product = source_lot.product if source_lot else None; target_product = form.cleaned_data.get('target_product'); target_payload = form.cleaned_data.get('new_target_product_payload')
        if target_payload:
            base_unit = target_product.unit if target_product else 'm3'; target_product, _ = Product.objects.get_or_create(name=target_payload['name'], defaults={'unit': base_unit, 'active': True})
        return source_product, target_product
    def _resolve_customer(self, form):
        new_name = (form.cleaned_data.get('new_customer_name') or '').strip()
        if new_name:
            customer, _ = Counterparty.objects.get_or_create(participant=self.request.user.participant, name=new_name, defaults={'type': 'customer'}); return customer
        return form.cleaned_data.get('customer')
    def form_valid(self, form):
        obj = form.save(commit=False); obj.created_by = self.request.user; obj.participant = self.request.user.participant; obj.customer = self._resolve_customer(form); obj.document_number = form.cleaned_data.get('document_number', ''); obj.supplier = None; obj.fsc_claim = ''; preferred_lot = form.cleaned_data['source_lot']; obj.source_product, obj.target_product = self._resolve_products(form); obj.source_unit = obj.source_product.unit; obj.source_quantity_base = form.cleaned_data['source_quantity_base']; obj.source_quantity = obj.source_quantity_base; obj.target_quantity_base = form.cleaned_data['target_quantity_base']; obj.target_unit_snapshot = obj.target_product.unit; obj.yield_factor_snapshot = form.cleaned_data['yield_factor_snapshot']
        try:
            with transaction.atomic(): obj.save(); reallocate_transformation_sources(obj, preferred_lot=preferred_lot); sync_transformation_metadata(obj); sync_transformation_target_lot(obj)
        except Exception as exc:
            form.add_error('source_lot', str(exc)); return self.form_invalid(form)
        messages.success(self.request, f'Transformação salva. Gerados {obj.target_quantity_base} {obj.target_product.get_unit_display()} de {obj.target_product}.'); return redirect(self.success_url)

class TransformationUpdateView(TransformationCreateView, UpdateView):
    model = TransformationRecord; success_url = reverse_lazy('transformation_list')
    def get_queryset(self): return TransformationRecord.objects.filter(participant=self.request.user.participant)
    def form_valid(self, form):
        obj = form.save(commit=False); obj.created_by = self.request.user; obj.participant = self.request.user.participant; obj.customer = self._resolve_customer(form); obj.document_number = form.cleaned_data.get('document_number', ''); obj.supplier = None; obj.fsc_claim = ''; preferred_lot = form.cleaned_data['source_lot']; obj.source_product, obj.target_product = self._resolve_products(form); obj.source_unit = obj.source_product.unit; obj.source_quantity_base = form.cleaned_data['source_quantity_base']; obj.source_quantity = obj.source_quantity_base; obj.target_quantity_base = form.cleaned_data['target_quantity_base']; obj.target_unit_snapshot = obj.target_product.unit; obj.yield_factor_snapshot = form.cleaned_data['yield_factor_snapshot']
        try:
            with transaction.atomic(): obj.save(); reallocate_transformation_sources(obj, preferred_lot=preferred_lot); sync_transformation_metadata(obj); sync_transformation_target_lot(obj)
        except Exception as exc:
            form.add_error('source_lot', str(exc)); return self.form_invalid(form)
        messages.success(self.request, 'Transformação atualizada com sucesso.'); return redirect(self.success_url)

class ManagerReviewEntryListView(PaginationMixin, ManagerRequiredMixin, ListView):
    model = EntryRecord; template_name = 'transactions/review_list.html'; context_object_name = 'records'
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return EntryRecord.objects.select_related('participant', 'product').filter(participant__organization=org) if org else EntryRecord.objects.none()

class ManagerReviewSaleListView(PaginationMixin, ManagerRequiredMixin, ListView):
    model = SaleRecord; template_name = 'transactions/review_list.html'; context_object_name = 'records'
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return SaleRecord.objects.select_related('participant', 'product').filter(participant__organization=org) if org else SaleRecord.objects.none()
