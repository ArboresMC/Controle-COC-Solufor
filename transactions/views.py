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




def _build_monthly_chart_data(entries_qs, sales_qs, transformations_qs, today):
    """Retorna dados dos últimos 6 meses para os gráficos do dashboard."""
    from datetime import date
    meses_pt = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
    months = []
    for i in range(5, -1, -1):
        # calcula o mês i meses atrás
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    labels = [meses_pt[m - 1] for y, m in months]
    entries_data = []
    sales_data = []
    transformations_data = []

    for y, m in months:
        entries_data.append(entries_qs.filter(movement_date__year=y, movement_date__month=m).count())
        sales_data.append(sales_qs.filter(movement_date__year=y, movement_date__month=m).count())
        transformations_data.append(transformations_qs.filter(movement_date__year=y, movement_date__month=m).count())

    return {
        'chart_labels': labels,
        'chart_entries': entries_data,
        'chart_sales': sales_data,
        'chart_transformations': transformations_data,
    }

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

        # Dados dos últimos 6 meses para os gráficos
        base_entries = EntryRecord.objects.all()
        base_sales = SaleRecord.objects.all()
        base_transformations = TransformationRecord.objects.all()
        if user.is_manager or user.is_auditor:
            if current_org:
                base_entries = base_entries.filter(participant__organization=current_org)
                base_sales = base_sales.filter(participant__organization=current_org)
                base_transformations = base_transformations.filter(participant__organization=current_org)
            else:
                base_entries = EntryRecord.objects.none()
                base_sales = SaleRecord.objects.none()
                base_transformations = TransformationRecord.objects.none()
        elif getattr(user, 'participant', None):
            base_entries = base_entries.filter(participant=user.participant)
            base_sales = base_sales.filter(participant=user.participant)
            base_transformations = base_transformations.filter(participant=user.participant)
        chart_data = _build_monthly_chart_data(base_entries, base_sales, base_transformations, today)
        data.update(chart_data)

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

            # Fechamentos aguardando aprovação do gestor
            pending_closings_count = closings_qs.filter(
                status=MonthlyClosing.STATUS_SUBMITTED
            ).count() if current_org else 0
            data['pending_closings_count'] = pending_closings_count

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
                'dashboard_alerts': get_manager_alerts(today=today, organization=current_org),
            })
        else:
            participant = getattr(user, 'participant', None)
            # Saldo único: considera todos os lançamentos (projetado)
            balance_items = get_balance_items(participant, projected=True) if participant else []

            # Fechamento do mês atual para o participante
            current_closing = None
            if participant:
                try:
                    current_closing = MonthlyClosing.objects.get(
                        participant=participant,
                        year=today.year,
                        month=today.month,
                    )
                except MonthlyClosing.DoesNotExist:
                    current_closing = None

            data.update({
                'balance_items': _serialize_balance_items(balance_items),
                'current_closing': current_closing,
                'dashboard_alerts': get_participant_alerts(participant, today=today) if participant else [],
                'balance_summary': {
                    'balance_count': len(balance_items),
                    'low_count': len([item for item in balance_items if item['status_class'] in ['warning', 'danger']]),
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


# =============================================================================
# GERENCIAMENTO DE DADOS — Gestor
# =============================================================================

from django.db import connection


def _delete_entries_sql(entry_ids):
    if not entry_ids:
        return 0
    ids = list(entry_ids)
    fmt = ','.join(['%s'] * len(ids))
    with connection.cursor() as c:
        # Coleta IDs antes de deletar qualquer coisa
        c.execute(f"""
            SELECT DISTINCT la.sale_id
            FROM transactions_lotallocation la
            JOIN transactions_tracelot tl ON la.lot_id = tl.id
            WHERE tl.entry_id IN ({fmt})
            AND la.sale_id IS NOT NULL
        """, ids)
        sale_ids = [row[0] for row in c.fetchall()]

        c.execute(f"""
            SELECT DISTINCT la.transformation_id
            FROM transactions_lotallocation la
            JOIN transactions_tracelot tl ON la.lot_id = tl.id
            WHERE tl.entry_id IN ({fmt})
            AND la.transformation_id IS NOT NULL
        """, ids)
        transformation_ids = [row[0] for row in c.fetchall()]

        # Agora deleta na ordem correta
        # 1. LotAllocations dos lotes de transformação originados dessas entradas
        if transformation_ids:
            tfmt = ','.join(['%s'] * len(transformation_ids))
            c.execute(f"""
                DELETE FROM transactions_lotallocation
                WHERE lot_id IN (
                    SELECT id FROM transactions_tracelot
                    WHERE transformation_id IN ({tfmt})
                )
            """, transformation_ids)
            c.execute(f"""
                DELETE FROM transactions_lotallocation
                WHERE transformation_id IN ({tfmt})
            """, transformation_ids)

        # 2. LotAllocations dos lotes de entrada
        c.execute(f"""
            DELETE FROM transactions_lotallocation
            WHERE lot_id IN (
                SELECT id FROM transactions_tracelot WHERE entry_id IN ({fmt})
            )
        """, ids)

        # 3. LotAllocations das saídas vinculadas
        if sale_ids:
            sfmt = ','.join(['%s'] * len(sale_ids))
            c.execute(f"DELETE FROM transactions_lotallocation WHERE sale_id IN ({sfmt})", sale_ids)

        # 4. TraceLots das transformações
        if transformation_ids:
            tfmt = ','.join(['%s'] * len(transformation_ids))
            c.execute(f"DELETE FROM transactions_tracelot WHERE transformation_id IN ({tfmt})", transformation_ids)

        # 5. TransformationRecords
        if transformation_ids:
            tfmt = ','.join(['%s'] * len(transformation_ids))
            c.execute(f"DELETE FROM transactions_transformationrecord WHERE id IN ({tfmt})", transformation_ids)

        # 6. SaleRecords
        if sale_ids:
            sfmt = ','.join(['%s'] * len(sale_ids))
            c.execute(f"DELETE FROM transactions_salerecord WHERE id IN ({sfmt})", sale_ids)

        # 7. TraceLots das entradas
        c.execute(f"DELETE FROM transactions_tracelot WHERE entry_id IN ({fmt})", ids)

        # 8. EntryRecords
        c.execute(f"DELETE FROM transactions_entryrecord WHERE id IN ({fmt})", ids)

    return len(ids)


def _delete_sales_sql(sale_ids):
    if not sale_ids:
        return 0
    ids = list(sale_ids)
    fmt = ','.join(['%s'] * len(ids))
    with connection.cursor() as c:
        c.execute(f"DELETE FROM transactions_lotallocation WHERE sale_id IN ({fmt})", ids)
        c.execute(f"DELETE FROM transactions_salerecord WHERE id IN ({fmt})", ids)
    return len(ids)


def _delete_transformations_sql(transformation_ids):
    if not transformation_ids:
        return 0
    ids = list(transformation_ids)
    fmt = ','.join(['%s'] * len(ids))
    with connection.cursor() as c:
        c.execute(f"""
            DELETE FROM transactions_lotallocation
            WHERE lot_id IN (
                SELECT id FROM transactions_tracelot WHERE transformation_id IN ({fmt})
            )
        """, ids)
        c.execute(f"DELETE FROM transactions_lotallocation WHERE transformation_id IN ({fmt})", ids)
        c.execute(f"DELETE FROM transactions_tracelot WHERE transformation_id IN ({fmt})", ids)
        c.execute(f"DELETE FROM transactions_transformationrecord WHERE id IN ({fmt})", ids)
    return len(ids)


class DataManagementView(ManagerRequiredMixin, TemplateView):
    template_name = 'transactions/data_management.html'

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        current_org = getattr(user, 'current_organization', None)

        participant_id = self.request.GET.get('participant')
        record_type = self.request.GET.get('type', 'entries')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        page = self.request.GET.get('page', 1)

        participants = Participant.objects.filter(
            status='active', organization=current_org
        ).order_by('trade_name', 'legal_name') if current_org else Participant.objects.none()

        selected_participant = participants.filter(pk=participant_id).first() if participant_id else None

        records_qs = None
        total_count = 0
        if selected_participant:
            if record_type == 'entries':
                records_qs = EntryRecord.objects.filter(
                    participant=selected_participant
                ).select_related('product', 'supplier').order_by('-movement_date', '-id')
            elif record_type == 'sales':
                records_qs = SaleRecord.objects.filter(
                    participant=selected_participant
                ).select_related('product', 'customer').order_by('-movement_date', '-id')
            elif record_type == 'transformations':
                records_qs = TransformationRecord.objects.filter(
                    participant=selected_participant
                ).select_related('source_product', 'target_product').order_by('-movement_date', '-id')

            if records_qs is not None:
                if date_from:
                    try:
                        from datetime import datetime
                        records_qs = records_qs.filter(movement_date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
                    except ValueError:
                        pass
                if date_to:
                    try:
                        from datetime import datetime
                        records_qs = records_qs.filter(movement_date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
                    except ValueError:
                        pass

                total_count = records_qs.count()
                paginator = Paginator(records_qs, 50)
                records_page = paginator.get_page(page)
            else:
                records_page = None
        else:
            records_page = None

        ctx.update({
            'participants': participants,
            'selected_participant': selected_participant,
            'record_type': record_type,
            'records': records_page,
            'total_count': total_count,
            'date_from': date_from,
            'date_to': date_to,
            'page_obj': records_page,
        })
        return ctx


class DataDeleteView(ManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        current_org = getattr(request.user, 'current_organization', None)
        action = request.POST.get('action')
        record_type = request.POST.get('record_type', 'entries')
        participant_id = request.POST.get('participant_id')

        participant = Participant.objects.filter(
            pk=participant_id, organization=current_org
        ).first() if participant_id and current_org else None

        if not participant:
            messages.error(request, 'Participante não encontrado.')
            return redirect('data_management')

        if action == 'delete_selected':
            selected_ids = request.POST.getlist('selected_ids')
            if not selected_ids:
                messages.warning(request, 'Nenhum registro selecionado.')
                return redirect(f'/transactions/gestor/dados/?participant={participant_id}&type={record_type}')
            ids = [int(i) for i in selected_ids if i.isdigit()]
            if record_type == 'entries':
                count = _delete_entries_sql(ids)
                messages.success(request, f'{count} entrada(s) excluída(s) com sucesso.')
            elif record_type == 'sales':
                count = _delete_sales_sql(ids)
                messages.success(request, f'{count} saída(s) excluída(s) com sucesso.')
            elif record_type == 'transformations':
                count = _delete_transformations_sql(ids)
                messages.success(request, f'{count} transformação(ões) excluída(s) com sucesso.')

        elif action == 'delete_all':
            if record_type == 'entries':
                ids = list(EntryRecord.objects.filter(participant=participant).values_list('id', flat=True))
                count = _delete_entries_sql(ids)
                messages.success(request, f'Todos os {count} registros de entradas de {participant} foram excluídos.')
            elif record_type == 'sales':
                ids = list(SaleRecord.objects.filter(participant=participant).values_list('id', flat=True))
                count = _delete_sales_sql(ids)
                messages.success(request, f'Todos os {count} registros de saídas de {participant} foram excluídos.')
            elif record_type == 'transformations':
                ids = list(TransformationRecord.objects.filter(participant=participant).values_list('id', flat=True))
                count = _delete_transformations_sql(ids)
                messages.success(request, f'Todos os {count} registros de transformações de {participant} foram excluídos.')

        return redirect(f'/transactions/gestor/dados/?participant={participant_id}&type={record_type}')


class DataDeleteSingleView(ManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        record_type = request.POST.get('record_type')
        record_id = request.POST.get('record_id')
        participant_id = request.POST.get('participant_id')

        if not record_id or not record_id.isdigit():
            messages.error(request, 'Registro inválido.')
            return redirect('data_management')

        rid = int(record_id)
        if record_type == 'entries':
            _delete_entries_sql([rid])
            messages.success(request, 'Entrada excluída com sucesso.')
        elif record_type == 'sales':
            _delete_sales_sql([rid])
            messages.success(request, 'Saída excluída com sucesso.')
        elif record_type == 'transformations':
            _delete_transformations_sql([rid])
            messages.success(request, 'Transformação excluída com sucesso.')

        return redirect(f'/transactions/gestor/dados/?participant={participant_id}&type={record_type}')
