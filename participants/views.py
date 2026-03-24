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
    model = Participant; template_name = 'participants/participant_list.html'; context_object_name = 'participants'
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return Participant.objects.filter(organization=org) if org else Participant.objects.none()

class ParticipantCreateView(ManagerRequiredMixin, CreateView):
    model = Participant; form_class = ParticipantForm; template_name = 'participants/participant_form.html'; success_url = reverse_lazy('participant_list')
    def form_valid(self, form):
        obj = form.save(commit=False); obj.organization = self.request.user.current_organization; obj.save(); messages.success(self.request, 'Participante criado com sucesso.'); self.object = obj; return super(CreateView, self).form_valid(form)
    def get_success_url(self): return self.success_url

class ParticipantUpdateView(ManagerRequiredMixin, UpdateView):
    model = Participant; form_class = ParticipantForm; template_name = 'participants/participant_form.html'; success_url = reverse_lazy('participant_list')
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return Participant.objects.filter(organization=org) if org else Participant.objects.none()
    def form_valid(self, form):
        obj = form.save(commit=False)
        if not obj.organization_id: obj.organization = self.request.user.current_organization
        obj.save(); messages.success(self.request, 'Participante atualizado com sucesso.'); self.object = obj; return super(UpdateView, self).form_valid(form)
    def get_success_url(self): return self.success_url
