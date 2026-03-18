from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from .forms import ParticipantForm
from .models import Participant


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager


class ParticipantListView(ManagerRequiredMixin, ListView):
    model = Participant
    template_name = 'participants/participant_list.html'
    context_object_name = 'participants'


class ParticipantCreateView(ManagerRequiredMixin, CreateView):
    model = Participant
    form_class = ParticipantForm
    template_name = 'participants/participant_form.html'
    success_url = reverse_lazy('participant_list')

    def form_valid(self, form):
        messages.success(self.request, 'Participante criado com sucesso.')
        return super().form_valid(form)


class ParticipantUpdateView(ManagerRequiredMixin, UpdateView):
    model = Participant
    form_class = ParticipantForm
    template_name = 'participants/participant_form.html'
    success_url = reverse_lazy('participant_list')

    def form_valid(self, form):
        messages.success(self.request, 'Participante atualizado com sucesso.')
        return super().form_valid(form)
