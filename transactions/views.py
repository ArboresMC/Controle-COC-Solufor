from datetime import date
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View
from catalog.models import Counterparty, Product
from compliance.models import MonthlyClosing
from participants.models import Participant
from .forms import EntryRecordForm, SaleRecordForm, TransformationRecordForm
from .models import EntryRecord, SaleRecord, TransformationRecord
from .services import convert_to_base, get_available_balance, get_balance_items, get_manager_alerts, get_participant_alerts, get_participant_balance_summary, reallocate_sale, reallocate_transformation_sources, sync_entry_lot, sync_transformation_metadata, sync_transformation_target_lot

class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager

def _serialize_balance_items(items):
    serialized = []
    for item in items:
        product = item.get('product')
        serialized.append({
            'product': str(product),
            'product_id': getattr(product, 'id', None),
            'balance': str(item.get('balance', 0)),
            'unit': item.get('unit', ''),
            'status_class': item.get('status_class', 'neutral'),
        })
    return serialized


def _build_top_products(entries_qs, sales_qs):
    entries_map = {row['product__name']: row['total'] for row in entries_qs.values('product__name').annotate(total=Sum('quantity_base')).order_by('-total')[:5]}
    sales_map = {row['product__name']: row['total'] for row in sales_qs.values('product__name').annotate(total=Sum('quantity_base')).order_by('-total')[:5]}
    names = []
    for name in list(entries_map.keys()) + list(sales_map.keys()):
        if name not in names:
            names.append(name)
    items = []
    for name in names[:5]:
        entry_total = entries_map.get(name) or 0
        sale_total = sales_map.get(name) or 0
        items.append({
            'name': name,
            'entry_total': entry_total,
            'sale_total': sale_total,
            'entry_bar': 0,
            'sale_bar': 0,
        })
    max_total = max([max(item['entry_total'], item['sale_total']) for item in items], default=0)
    for item in items:
        item['entry_bar'] = int((item['entry_total'] / max_total) * 100) if max_total else 0
        item['sale_bar'] = int((item['sale_total'] / max_total) * 100) if max_total else 0
    return items


def _base_dashboard_context(user, today):
    current_org = getattr(user, 'current_organization', None)
    month_entries = EntryRecord.objects.select_related('participant', 'product')
    month_sales = SaleRecord.objects.select_related('participant', 'product')
    transformations = TransformationRecord.objects.select_related('participant', 'source_product', 'target_product', 'customer', 'supplier')
    closings = MonthlyClosing.objects.select_related('participant').filter(year=today.year, month=today.month)

    if user.is_manager or user.is_auditor:
        if current_org:
            month_entries = month_entries.filter(participant__organization=current_org)
            month_sales = month_sales.filter(participant__organization=current_org)
            transformations = transformations.filter(participant__organization=current_org)
            closings = closings.filter(participant__organization=current_org)
        else:
            month_entries = EntryRecord.objects.none()
            month_sales = SaleRecord.objects.none()
            transformations = TransformationRecord.objects.none()
            closings = MonthlyClosing.objects.none()
    elif getattr(user, 'participant', None):
        month_entries = month_entries.filter(participant=user.participant)
        month_sales = month_sales.filter(participant=user.participant)
        transformations = transformations.filter(participant=user.participant)
        closings = closings.filter(participant=user.participant)
    else:
        month_entries = EntryRecord.objects.none()
        month_sales = SaleRecord.objects.none()
        transformations = TransformationRecord.objects.none()
        closings = MonthlyClosing.objects.none()

    month_entries = month_entries.filter(movement_date__year=today.year, movement_date__month=today.month)
    month_sales = month_sales.filter(movement_date__year=today.year, movement_date__month=today.month)
    transformations = transformations.filter(movement_date__year=today.year, movement_date__month=today.month)
    return current_org, month_entries, month_sales, transformations, closings


def _dashboard_cache_key(user, today):
    org = getattr(user, 'current_organization', None)
    participant = getattr(user, 'participant', None)
    return f"dashboard:v2:user:{user.id}:org:{getattr(org, 'id', 'none')}:participant:{getattr(participant, 'id', 'none')}:month:{today:%Y-%m}"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()
        current_org, month_entries, month_sales, transformations, closings = _base_dashboard_context(user, today)

        ctx['current_closings'] = closings
        ctx['recent_entries'] = month_entries.order_by('-movement_date', '-id')[:5]
        ctx['recent_sales'] = month_sales.order_by('-movement_date', '-id')[:5]
        ctx['recent_transformations'] = transformations.order_by('-movement_date', '-id')[:5]

        cache_key = _dashboard_cache_key(user, today)
        cached = cache.get(cache_key)
        if cached:
            ctx.update(cached)
            return ctx

        entries_count = month_entries.count()
        sales_count = month_sales.count()
        transformations_count = transformations.count()
        entries_total = month_entries.aggregate(total=Sum('quantity_base'))['total'] or 0
        sales_total = month_sales.aggregate(total=Sum('quantity_base'))['total'] or 0
        transformations_total = transformations.aggregate(total=Sum('target_quantity_base'))['total'] or 0
        needs_correction = month_entries.filter(status='needs_correction').count() + month_sales.filter(status='needs_correction').count()
        movement_total = entries_count + sales_count + transformations_count

        data = {
            'entries_count': entries_count,
            'sales_count': sales_count,
            'transformations_count': transformations_count,
            'entries_total': entries_total,
            'sales_total': sales_total,
            'transformations_total': transformations_total,
            'needs_correction': needs_correction,
            'movement_total': movement_total,
            'entry_share': int((entries_count / movement_total) * 100) if movement_total else 0,
            'sale_share': int((sales_count / movement_total) * 100) if movement_total else 0,
            'transformation_share': int((transformations_count / movement_total) * 100) if movement_total else 0,
            'top_products': _build_top_products(month_entries, month_sales),
        }

        # Totais históricos — desde o início, sem filtro de mês
        all_entries = EntryRecord.objects.select_related('participant', 'product')
        all_sales = SaleRecord.objects.select_related('participant', 'product')
        all_transformations = TransformationRecord.objects.select_related('participant')
        if user.is_manager or user.is_auditor:
            if current_org:
                all_entries = all_entries.filter(participant__organization=current_org)
                all_sales = all_sales.filter(participant__organization=current_org)
                all_transformations = all_transformations.filter(participant__organization=current_org)
            else:
                all_entries = EntryRecord.objects.none()
                all_sales = SaleRecord.objects.none()
                all_transformations = TransformationRecord.objects.none()
        elif getattr(user, 'participant', None):
            all_entries = all_entries.filter(participant=user.participant)
            all_sales = all_sales.filter(participant=user.participant)
            all_transformations = all_transformations.filter(participant=user.participant)
        else:
            all_entries = EntryRecord.objects.none()
            all_sales = SaleRecord.objects.none()
            all_transformations = TransformationRecord.objects.none()

        data.update({
            'hist_entries_count': all_entries.count(),
            'hist_sales_count': all_sales.count(),
            'hist_transformations_count': all_transformations.count(),
            'hist_entries_total': all_entries.aggregate(total=Sum('quantity_base'))['total'] or 0,
            'hist_sales_total': all_sales.aggregate(total=Sum('quantity_base'))['total'] or 0,
            'hist_transformations_total': all_transformations.aggregate(total=Sum('target_quantity_base'))['total'] or 0,
        })

        if user.is_manager:
            active_participants = Participant.objects.filter(status='active')
            active_participants = active_participants.filter(organization=current_org) if current_org else Participant.objects.none()
            closings_qs = MonthlyClosing.objects.filter(year=today.year, month=today.month)
            closings_qs = closings_qs.filter(participant__organization=current_org) if current_org else MonthlyClosing.objects.none()

            # Conta total de registros submitted aguardando aprovação
            pending_entries = EntryRecord.objects.filter(
                participant__organization=current_org, status='submitted'
            ).count() if current_org else 0
            pending_sales = SaleRecord.objects.filter(
                participant__organization=current_org, status='submitted'
            ).count() if current_org else 0
            data['pending_submissions_count'] = pending_entries + pending_sales

            participant_summaries = []
            for participant in active_participants.order_by('trade_name', 'legal_name')[:8]:
                summary = get_participant_balance_summary(participant)
                participant_summaries.append({
                    'participant_name': str(participant),
                    'participant_id': participant.id,
                    'balance_count': summary['balance_count'],
                    'low_count': summary['low_count'],
                })

            without_closing_qs = active_participants.exclude(id__in=closings_qs.values_list('participant_id', flat=True))
            data.update({
                'manager_metrics': {
                    'participants_active': active_participants.count(),
                    'participants_without_closing': without_closing_qs.count(),
                    'closings_submitted': closings_qs.filter(status='submitted').count(),
                    'closings_rejected': closings_qs.filter(status='rejected').count(),
                    'low_balance_participants': len([s for s in participant_summaries if s['low_count']]),
                },
                'participant_summaries': participant_summaries,
                'participants_without_closing': [str(p) for p in without_closing_qs[:10]],
                'balance_items': [],
                'projected_balance_items': [],
                'dashboard_alerts': get_manager_alerts(today=today, organization=current_org),
            })
        else:
            participant = getattr(user, 'participant', None)
            balance_items = get_balance_items(participant, projected=False) if participant else []
            projected_balance_items = get_balance_items(participant, projected=True) if participant else []
            data.update({
                'balance_items': _serialize_balance_items(balance_items),
                'projected_balance_items': _serialize_balance_items(projected_balance_items),
                'dashboard_alerts': get_participant_alerts(participant, today=today) if participant else [],
                'balance_summary': {
                    'validated_count': len(balance_items),
                    'projected_count': len(projected_balance_items),
                    'low_count': len([item for item in projected_balance_items if item['status_class'] in ['warning', 'danger']]),
                }
            })

        cache.set(cache_key, data, 120)
        ctx.update(data)
        return ctx

class ParticipantScopedMixin(LoginRequiredMixin):
    def get_queryset(self):
        qs = self.model.objects.select_related('participant', 'product')
        user = self.request.user
        current_org = getattr(user, 'current_organization', None)
        if user.is_manager or user.is_auditor:
            return qs.filter(participant__organization=current_org) if current_org else qs.none()
        if user.participant: return qs.filter(participant=user.participant)
        return qs.none()

class DocumentCenterView(LoginRequiredMixin, TemplateView):
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

        ctx['entry_docs'] = self._filter_docs(entry_qs).order_by('-movement_date', '-id')[:100]
        ctx['sale_docs'] = self._filter_docs(sale_qs).order_by('-movement_date', '-id')[:100]
        ctx['transformation_docs'] = self._filter_docs(transformation_qs).order_by('-movement_date', '-id')[:100]
        return ctx

class EntryListView(ParticipantScopedMixin, ListView):
    model = EntryRecord; template_name = 'transactions/entry_list.html'; context_object_name = 'records'; paginate_by = 50

class SaleListView(ParticipantScopedMixin, ListView):
    model = SaleRecord; template_name = 'transactions/sale_list.html'; context_object_name = 'records'; paginate_by = 50

class TransformationListView(LoginRequiredMixin, ListView):
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

class ManagerReviewEntryListView(ManagerRequiredMixin, ListView):
    model = EntryRecord; template_name = 'transactions/review_list.html'; context_object_name = 'records'
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return EntryRecord.objects.select_related('participant', 'product').filter(participant__organization=org) if org else EntryRecord.objects.none()

class ManagerReviewSaleListView(ManagerRequiredMixin, ListView):
    model = SaleRecord; template_name = 'transactions/review_list.html'; context_object_name = 'records'
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return SaleRecord.objects.select_related('participant', 'product').filter(participant__organization=org) if org else SaleRecord.objects.none()


class ManagerReviewDashboardView(ManagerRequiredMixin, TemplateView):
    """Lista participantes com registros pendentes de aprovação (submitted)."""
    template_name = 'transactions/review_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = getattr(self.request.user, 'current_organization', None)
        if not org:
            ctx['pending_participants'] = []
            return ctx

        from django.db.models import Count, Q
        participants = Participant.objects.filter(
            organization=org, status='active'
        ).annotate(
            pending_entries=Count('entries', filter=Q(entries__status='submitted')),
            pending_sales=Count('sales', filter=Q(sales__status='submitted')),
        ).filter(
            Q(pending_entries__gt=0) | Q(pending_sales__gt=0)
        ).order_by('legal_name')

        ctx['pending_participants'] = participants
        return ctx


class BulkApproveView(ManagerRequiredMixin, View):
    """Aprova em lote todos os registros submitted de um participante."""

    def post(self, request, *args, **kwargs):
        from django.db.models import Q
        participant_id = request.POST.get('participant_id')
        org = getattr(request.user, 'current_organization', None)
        if not org or not participant_id:
            messages.error(request, 'Requisição inválida.')
            return redirect('manager_review_dashboard')

        participant = Participant.objects.filter(pk=participant_id, organization=org).first()
        if not participant:
            messages.error(request, 'Participante não encontrado.')
            return redirect('manager_review_dashboard')

        entries_updated = EntryRecord.objects.filter(
            participant=participant, status='submitted'
        ).update(status='reviewed')

        sales_updated = SaleRecord.objects.filter(
            participant=participant, status='submitted'
        ).update(status='reviewed')

        # Invalida cache do dashboard do participante
        from django.core.cache import cache
        from datetime import date
        today = date.today()
        cache_key = f"dashboard:v2:user:*:org:{org.id}:participant:{participant.id}:month:{today:%Y-%m}"
        cache.clear()

        total = entries_updated + sales_updated
        messages.success(
            request,
            f'{total} registro(s) de {participant} aprovado(s). '
            f'({entries_updated} entradas, {sales_updated} saídas)'
        )
        return redirect('manager_review_dashboard')
