from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View
from django.db import connection

from .forms import EspecieForm, PropriedadeForm, InventarioEntradaForm, SaidaManejoForm
from .models import Especie, Propriedade, InventarioEntrada, SaidaManejo


class FMAccessMixin(LoginRequiredMixin):
    """Garante que só usuários com acesso a Manejo Florestal (FM) entrem nessas telas."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_manager or user.is_auditor:
            return super().dispatch(request, *args, **kwargs)
        participant = getattr(user, 'participant', None)
        if not participant or not participant.ativo_fm:
            messages.error(request, 'Seu cadastro não tem acesso ao módulo de Manejo Florestal.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_participant(self):
        user = self.request.user
        if user.is_manager or user.is_auditor:
            participant_id = self.request.GET.get('participant')
            if participant_id:
                from participants.models import Participant
                return Participant.objects.filter(pk=participant_id, ativo_fm=True).first()
            return None
        return getattr(user, 'participant', None)


class ManejoManagerRequiredMixin(LoginRequiredMixin):
    """Restringe acesso a telas administrativas do Manejo (gestão de dados,
    inativação de propriedades) apenas a gestores/auditores."""

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and (request.user.is_manager or request.user.is_auditor)):
            messages.error(request, 'Apenas o gestor pode acessar esta área.')
            return redirect('manejo_dashboard')
        return super().dispatch(request, *args, **kwargs)


def _build_participant_context(participant):
    """Monta o contexto de saldo/inventário de UM participante FM. Usado tanto
    pelo painel direto do participante quanto pelo drill-in do gestor."""
    entradas = InventarioEntrada.objects.filter(participant=participant).select_related('propriedade', 'especie').com_saldo()
    saldo_rows = []
    total_inicial = Decimal('0')
    total_saldo = Decimal('0')
    for entrada in entradas:
        saldo = entrada.saldo_disponivel_m3
        total_inicial += entrada.volume_m3
        total_saldo += saldo
        saldo_rows.append({
            'entrada': entrada,
            'propriedade': entrada.propriedade.nome,
            'especie': entrada.especie.nome,
            'volume_inicial': entrada.volume_m3,
            'volume_vendido': entrada.volume_vendido_m3,
            'saldo': saldo,
        })

    recent_saidas = SaidaManejo.objects.filter(participant=participant).exclude(
        documento='AJUSTE-HISTORICO'
    ).select_related('entrada__propriedade', 'entrada__especie').order_by('-data', '-id')[:10]

    return {
        'saldo_rows': saldo_rows,
        'total_inicial': total_inicial,
        'total_saldo': total_saldo,
        'total_propriedades': Propriedade.objects.filter(participant=participant, ativa=True).count(),
        'total_especies': Especie.objects.filter(participant=participant, ativo=True).count(),
        'recent_saidas': recent_saidas,
    }


def _build_chart_data(membros_qs, today):
    """Gráfico dos últimos 6 meses: entradas de inventário e saídas reais
    (exclui ajustes históricos) agregadas entre os membros informados.

    Otimizado para 2 queries agrupadas (em vez de 12 queries, uma por mês)
    e cacheado por 10 minutos — o mês corrente pode ficar levemente
    desatualizado nesse intervalo, mas evita recalcular o histórico
    completo a cada carregamento do painel."""
    from django.core.cache import cache
    from django.db.models import Count
    from django.db.models.functions import TruncMonth

    membros_ids = tuple(sorted(membros_qs.values_list('id', flat=True)))
    cache_key = f"fm_chart:{hash(membros_ids)}:{today.year}:{today.month}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    meses_pt = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    months = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    inicio = date(months[0][0], months[0][1], 1)
    labels = [meses_pt[m - 1] for y, m in months]

    entradas_por_mes = {
        row['mes']: row['total']
        for row in InventarioEntrada.objects.filter(participant__in=membros_ids, data__gte=inicio)
        .annotate(mes=TruncMonth('data')).values('mes').annotate(total=Count('id')).values('mes', 'total')
    }
    saidas_por_mes = {
        row['mes']: row['total']
        for row in SaidaManejo.objects.filter(participant__in=membros_ids, data__gte=inicio)
        .exclude(documento='AJUSTE-HISTORICO')
        .annotate(mes=TruncMonth('data')).values('mes').annotate(total=Count('id')).values('mes', 'total')
    }

    entradas_data = [entradas_por_mes.get(date(y, m, 1), 0) for y, m in months]
    saidas_data = [saidas_por_mes.get(date(y, m, 1), 0) for y, m in months]

    result = {
        'fm_chart_labels': labels,
        'fm_chart_entradas': entradas_data,
        'fm_chart_saidas': saidas_data,
    }
    cache.set(cache_key, result, 600)  # 10 minutos
    return result


class ManejoDashboardView(FMAccessMixin, TemplateView):
    """Painel principal de Manejo Florestal.
    Gestor/auditor: visão agregada de TODOS os membros FM.
    Participante: visão direta dos seus próprios dados (sem agregação)."""
    template_name = 'manejo/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_manager or user.is_auditor:
            from participants.models import Participant
            current_org = getattr(user, 'current_organization', None)
            membros_fm = Participant.objects.filter(ativo_fm=True, status='active')
            membros_fm = membros_fm.filter(organization=current_org) if current_org else Participant.objects.none()

            propriedades = Propriedade.objects.filter(participant__in=membros_fm, ativa=True)
            entradas = InventarioEntrada.objects.filter(participant__in=membros_fm).select_related(
                'propriedade', 'especie', 'participant'
            ).com_saldo()

            total_volume = Decimal('0')
            total_saldo = Decimal('0')
            por_membro = {}
            for entrada in entradas:
                saldo = entrada.saldo_disponivel_m3
                total_volume += entrada.volume_m3
                total_saldo += saldo
                pid = entrada.participant_id
                if pid not in por_membro:
                    por_membro[pid] = {
                        'nome': str(entrada.participant),
                        'volume': Decimal('0'),
                        'saldo': Decimal('0'),
                        'propriedades': set(),
                    }
                por_membro[pid]['volume'] += entrada.volume_m3
                por_membro[pid]['saldo'] += saldo
                por_membro[pid]['propriedades'].add(entrada.propriedade_id)

            membro_rows = sorted(
                [
                    {
                        'participant_id': pid,
                        'nome': info['nome'],
                        'propriedades_count': len(info['propriedades']),
                        'volume': info['volume'],
                        'saldo': info['saldo'],
                    }
                    for pid, info in por_membro.items()
                ],
                key=lambda r: r['nome']
            )

            from django.core.paginator import Paginator
            page = self.request.GET.get('page', 1)
            paginator = Paginator(membro_rows, 15)
            membro_rows_page = paginator.get_page(page)

            recent_saidas = SaidaManejo.objects.filter(participant__in=membros_fm).exclude(
                documento='AJUSTE-HISTORICO'
            ).select_related('entrada__propriedade', 'entrada__especie', 'participant').order_by('-data', '-id')[:10]

            ctx.update({
                'is_aggregate': True,
                'total_membros': membros_fm.count(),
                'total_propriedades': propriedades.count(),
                'total_volume': total_volume,
                'total_saldo': total_saldo,
                'membro_rows': membro_rows_page,
                'recent_saidas': recent_saidas,
            })
            ctx.update(_build_chart_data(membros_fm, date.today()))
            return ctx

        # Participante: mostra direto os próprios dados, sem agregação
        participant = getattr(user, 'participant', None)
        ctx['is_aggregate'] = False
        if not participant or not participant.ativo_fm:
            ctx['require_filter'] = True
            return ctx
        ctx.update(_build_participant_context(participant))
        ctx.update(_build_chart_data(
            type(participant).objects.filter(pk=participant.pk), date.today()
        ))
        return ctx


class ManejoParticipantDashboardView(FMAccessMixin, TemplateView):
    """Visão detalhada de UM participante FM específico — usada pelo gestor
    para 'entrar' em um membro a partir do painel agregado."""
    template_name = 'manejo/participante_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_manager or user.is_auditor:
            from participants.models import Participant
            ctx['participants'] = Participant.objects.filter(ativo_fm=True, status='active').order_by('trade_name')
            participant = self.get_participant()
            ctx['selected_participant'] = participant
            if not participant:
                ctx['require_filter'] = True
                return ctx
        else:
            participant = self.get_participant()

        ctx.update(_build_participant_context(participant))
        return ctx


# --- Espécies ---

class EspecieListView(FMAccessMixin, ListView):
    template_name = 'manejo/especie_list.html'
    context_object_name = 'especies'

    def get_queryset(self):
        participant = self.get_participant()
        if not participant:
            return Especie.objects.none()
        return Especie.objects.filter(participant=participant).order_by('nome')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_manager or user.is_auditor:
            from participants.models import Participant
            ctx['participants'] = Participant.objects.filter(ativo_fm=True, status='active').order_by('trade_name')
        ctx['selected_participant'] = self.get_participant()
        return ctx


class EspecieCreateView(FMAccessMixin, CreateView):
    model = Especie
    form_class = EspecieForm
    template_name = 'manejo/especie_form.html'
    success_url = reverse_lazy('manejo_especie_list')

    def form_valid(self, form):
        form.instance.participant = self.get_participant()
        messages.success(self.request, 'Espécie cadastrada com sucesso.')
        return super().form_valid(form)


class EspecieUpdateView(FMAccessMixin, UpdateView):
    model = Especie
    form_class = EspecieForm
    template_name = 'manejo/especie_form.html'
    success_url = reverse_lazy('manejo_especie_list')

    def get_queryset(self):
        return Especie.objects.filter(participant=self.get_participant())

    def form_valid(self, form):
        messages.success(self.request, 'Espécie atualizada com sucesso.')
        return super().form_valid(form)


# --- Propriedades ---

class PropriedadeListView(FMAccessMixin, ListView):
    template_name = 'manejo/propriedade_list.html'
    context_object_name = 'propriedades'

    def get_queryset(self):
        participant = self.get_participant()
        if not participant:
            return Propriedade.objects.none()
        return Propriedade.objects.filter(participant=participant).order_by('nome')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_manager or user.is_auditor:
            from participants.models import Participant
            ctx['participants'] = Participant.objects.filter(ativo_fm=True, status='active').order_by('trade_name')
        ctx['selected_participant'] = self.get_participant()
        return ctx


class PropriedadeCreateView(FMAccessMixin, CreateView):
    model = Propriedade
    form_class = PropriedadeForm
    template_name = 'manejo/propriedade_form.html'
    success_url = reverse_lazy('manejo_propriedade_list')

    def form_valid(self, form):
        form.instance.participant = self.get_participant()
        messages.success(self.request, 'Propriedade cadastrada com sucesso.')
        return super().form_valid(form)


class PropriedadeUpdateView(FMAccessMixin, UpdateView):
    model = Propriedade
    form_class = PropriedadeForm
    template_name = 'manejo/propriedade_form.html'
    success_url = reverse_lazy('manejo_propriedade_list')

    def get_queryset(self):
        return Propriedade.objects.filter(participant=self.get_participant())

    def form_valid(self, form):
        messages.success(self.request, 'Propriedade atualizada com sucesso.')
        return super().form_valid(form)


# --- Entradas de inventário ---

class InventarioEntradaListView(FMAccessMixin, ListView):
    template_name = 'manejo/entrada_list.html'
    context_object_name = 'entradas'
    paginate_by = 25

    def get_queryset(self):
        participant = self.get_participant()
        if not participant:
            return InventarioEntrada.objects.none()
        return InventarioEntrada.objects.filter(participant=participant).select_related('propriedade', 'especie').com_saldo()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_manager or user.is_auditor:
            from participants.models import Participant
            ctx['participants'] = Participant.objects.filter(ativo_fm=True, status='active').order_by('trade_name')
        ctx['selected_participant'] = self.get_participant()
        return ctx


class InventarioEntradaCreateView(FMAccessMixin, CreateView):
    model = InventarioEntrada
    form_class = InventarioEntradaForm
    template_name = 'manejo/entrada_form.html'
    success_url = reverse_lazy('manejo_entrada_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.get_participant()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Entrada de inventário registrada com sucesso.')
        return super().form_valid(form)


# --- Saídas ---

class SaidaManejoListView(FMAccessMixin, ListView):
    template_name = 'manejo/saida_list.html'
    context_object_name = 'saidas'
    paginate_by = 25

    def get_queryset(self):
        participant = self.get_participant()
        if not participant:
            return SaidaManejo.objects.none()
        return SaidaManejo.objects.filter(participant=participant).select_related(
            'entrada__propriedade', 'entrada__especie'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_manager or user.is_auditor:
            from participants.models import Participant
            ctx['participants'] = Participant.objects.filter(ativo_fm=True, status='active').order_by('trade_name')
        ctx['selected_participant'] = self.get_participant()
        return ctx


class SaidaManejoCreateView(FMAccessMixin, CreateView):
    model = SaidaManejo
    form_class = SaidaManejoForm
    template_name = 'manejo/saida_form.html'
    success_url = reverse_lazy('manejo_saida_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['participant'] = self.get_participant()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Saída registrada com sucesso.')
        return super().form_valid(form)


# =============================================================================
# GESTÃO DE DADOS — Manejo Florestal (apenas gestor)
# =============================================================================

def _delete_entradas_sql(entrada_ids):
    """Exclui InventarioEntrada e, antes, as SaidaManejo vinculadas
    (entrada.PROTECT exige isso). Coleta os IDs dependentes antes de
    deletar, na mesma lógica já usada em transactions._delete_entries_sql."""
    if not entrada_ids:
        return 0, 0
    ids = list(entrada_ids)
    fmt = ','.join(['%s'] * len(ids))
    with connection.cursor() as c:
        c.execute(f"SELECT id FROM manejo_saidamanejo WHERE entrada_id IN ({fmt})", ids)
        saida_ids = [row[0] for row in c.fetchall()]

        if saida_ids:
            sfmt = ','.join(['%s'] * len(saida_ids))
            c.execute(f"DELETE FROM manejo_saidamanejo WHERE id IN ({sfmt})", saida_ids)

        c.execute(f"DELETE FROM manejo_inventarioentrada WHERE id IN ({fmt})", ids)

    return len(ids), len(saida_ids)


def _delete_saidas_sql(saida_ids):
    """Exclui SaidaManejo. Não há dependentes (nada referencia SaidaManejo via FK)."""
    if not saida_ids:
        return 0
    ids = list(saida_ids)
    fmt = ','.join(['%s'] * len(ids))
    with connection.cursor() as c:
        c.execute(f"DELETE FROM manejo_saidamanejo WHERE id IN ({fmt})", ids)
    return len(ids)


class ManejoDataManagementView(ManejoManagerRequiredMixin, TemplateView):
    template_name = 'manejo/data_management.html'

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator
        from participants.models import Participant
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        current_org = getattr(user, 'current_organization', None)

        participant_id = self.request.GET.get('participant')
        record_type = self.request.GET.get('type', 'propriedades')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        page = self.request.GET.get('page', 1)

        participants = Participant.objects.filter(
            ativo_fm=True, status='active', organization=current_org
        ).order_by('trade_name', 'legal_name') if current_org else Participant.objects.none()

        selected_participant = participants.filter(pk=participant_id).first() if participant_id else None

        records_page = None
        total_count = 0
        if selected_participant:
            records_qs = None
            if record_type == 'propriedades':
                records_qs = Propriedade.objects.filter(
                    participant=selected_participant, ativa=True
                ).order_by('nome')
            elif record_type == 'entradas':
                records_qs = InventarioEntrada.objects.filter(
                    participant=selected_participant
                ).select_related('propriedade', 'especie').com_saldo().order_by('-data', '-id')
            elif record_type == 'saidas':
                records_qs = SaidaManejo.objects.filter(
                    participant=selected_participant
                ).select_related('entrada__propriedade', 'entrada__especie').order_by('-data', '-id')

            if records_qs is not None:
                if record_type in ('entradas', 'saidas'):
                    if date_from:
                        try:
                            from datetime import datetime
                            records_qs = records_qs.filter(data__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
                        except ValueError:
                            pass
                    if date_to:
                        try:
                            from datetime import datetime
                            records_qs = records_qs.filter(data__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
                        except ValueError:
                            pass

                total_count = records_qs.count()
                paginator = Paginator(records_qs, 50)
                records_page = paginator.get_page(page)

        ctx.update({
            'participants': participants,
            'selected_participant': selected_participant,
            'record_type': record_type,
            'records': records_page,
            'total_count': total_count,
            'date_from': date_from,
            'date_to': date_to,
        })
        return ctx


class ManejoDataDeactivateView(ManejoManagerRequiredMixin, View):
    """Inativa (não exclui) Propriedade(s) — individual ou em lote.
    Propriedade tem on_delete=PROTECT a partir de InventarioEntrada,
    então exclusão de verdade quebraria o histórico FSC; inativar é o
    caminho correto para "encerrar" uma área sem perder rastreabilidade."""

    def post(self, request, *args, **kwargs):
        participant_id = request.POST.get('participant_id')
        action = request.POST.get('action')

        if action == 'deactivate_selected':
            selected_ids = request.POST.getlist('selected_ids')
            ids = [int(i) for i in selected_ids if i.isdigit()]
            if not ids:
                messages.warning(request, 'Nenhuma propriedade selecionada.')
            else:
                count = Propriedade.objects.filter(pk__in=ids).update(ativa=False)
                messages.success(request, f'{count} propriedade(s) inativada(s) com sucesso.')

        elif action == 'deactivate_single':
            record_id = request.POST.get('record_id')
            if record_id and record_id.isdigit():
                updated = Propriedade.objects.filter(pk=int(record_id)).update(ativa=False)
                if updated:
                    messages.success(request, 'Propriedade inativada com sucesso.')
                else:
                    messages.error(request, 'Propriedade não encontrada.')

        return redirect(f'/manejo/gestor/dados/?participant={participant_id}&type=propriedades')


class ManejoDataDeleteView(ManejoManagerRequiredMixin, View):
    """Exclusão (em lote ou total) de Entradas de Inventário ou Saídas de Manejo."""

    def post(self, request, *args, **kwargs):
        record_type = request.POST.get('record_type')
        participant_id = request.POST.get('participant_id')
        action = request.POST.get('action')

        from participants.models import Participant
        participant = Participant.objects.filter(pk=participant_id, ativo_fm=True).first() if participant_id else None
        if not participant:
            messages.error(request, 'Participante não encontrado.')
            return redirect('manejo_data_management')

        if action == 'delete_selected':
            selected_ids = request.POST.getlist('selected_ids')
            ids = [int(i) for i in selected_ids if i.isdigit()]
            if not ids:
                messages.warning(request, 'Nenhum registro selecionado.')
            elif record_type == 'entradas':
                count, saidas_count = _delete_entradas_sql(ids)
                extra = f' (e {saidas_count} saída(s) vinculada(s))' if saidas_count else ''
                messages.success(request, f'{count} entrada(s) excluída(s) com sucesso{extra}.')
            elif record_type == 'saidas':
                count = _delete_saidas_sql(ids)
                messages.success(request, f'{count} saída(s) excluída(s) com sucesso.')

        elif action == 'delete_all':
            if record_type == 'entradas':
                ids = list(InventarioEntrada.objects.filter(participant=participant).values_list('id', flat=True))
                count, saidas_count = _delete_entradas_sql(ids)
                extra = f' (e {saidas_count} saída(s) vinculada(s))' if saidas_count else ''
                messages.success(request, f'Todas as {count} entradas de {participant} foram excluídas{extra}.')
            elif record_type == 'saidas':
                ids = list(SaidaManejo.objects.filter(participant=participant).values_list('id', flat=True))
                count = _delete_saidas_sql(ids)
                messages.success(request, f'Todas as {count} saídas de {participant} foram excluídas.')

        return redirect(f'/manejo/gestor/dados/?participant={participant_id}&type={record_type}')


class ManejoDataDeleteSingleView(ManejoManagerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        record_type = request.POST.get('record_type')
        record_id = request.POST.get('record_id')
        participant_id = request.POST.get('participant_id')

        if not record_id or not record_id.isdigit():
            messages.error(request, 'Registro inválido.')
            return redirect('manejo_data_management')

        rid = int(record_id)
        if record_type == 'entradas':
            count, saidas_count = _delete_entradas_sql([rid])
            extra = f' (e {saidas_count} saída(s) vinculada(s))' if saidas_count else ''
            messages.success(request, f'Entrada excluída com sucesso{extra}.')
        elif record_type == 'saidas':
            _delete_saidas_sql([rid])
            messages.success(request, 'Saída excluída com sucesso.')

        return redirect(f'/manejo/gestor/dados/?participant={participant_id}&type={record_type}')
