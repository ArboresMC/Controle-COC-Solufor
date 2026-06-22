from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

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


class ManejoDashboardView(FMAccessMixin, TemplateView):
    template_name = 'manejo/dashboard.html'

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

        entradas = InventarioEntrada.objects.filter(participant=participant).select_related('propriedade', 'especie')
        saldo_rows = []
        total_inicial = 0
        total_saldo = 0
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

        recent_saidas = SaidaManejo.objects.filter(participant=participant).select_related(
            'entrada__propriedade', 'entrada__especie'
        ).order_by('-data', '-id')[:10]

        ctx.update({
            'saldo_rows': saldo_rows,
            'total_inicial': total_inicial,
            'total_saldo': total_saldo,
            'total_propriedades': Propriedade.objects.filter(participant=participant, ativa=True).count(),
            'total_especies': Especie.objects.filter(participant=participant, ativo=True).count(),
            'recent_saidas': recent_saidas,
        })
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

    def get_queryset(self):
        participant = self.get_participant()
        if not participant:
            return InventarioEntrada.objects.none()
        return InventarioEntrada.objects.filter(participant=participant).select_related('propriedade', 'especie')

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

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response


# --- Saídas ---

class SaidaManejoListView(FMAccessMixin, ListView):
    template_name = 'manejo/saida_list.html'
    context_object_name = 'saidas'

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
