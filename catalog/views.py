from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from .forms import ProductForm, CounterpartyForm
from .models import Product, Counterparty


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager


class ProductListView(ManagerRequiredMixin, ListView):
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'


class ProductCreateView(ManagerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produto criado com sucesso.')
        return super().form_valid(form)


class ProductUpdateView(ManagerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produto atualizado com sucesso.')
        return super().form_valid(form)


class CounterpartyListView(ManagerRequiredMixin, ListView):
    model = Counterparty
    template_name = 'catalog/counterparty_list.html'
    context_object_name = 'counterparties'
    queryset = Counterparty.objects.select_related('participant').order_by('name')


class CounterpartyCreateView(ManagerRequiredMixin, CreateView):
    model = Counterparty
    form_class = CounterpartyForm
    template_name = 'catalog/counterparty_form.html'
    success_url = reverse_lazy('counterparty_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente/fornecedor criado com sucesso.')
        return super().form_valid(form)


class CounterpartyUpdateView(ManagerRequiredMixin, UpdateView):
    model = Counterparty
    form_class = CounterpartyForm
    template_name = 'catalog/counterparty_form.html'
    success_url = reverse_lazy('counterparty_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente/fornecedor atualizado com sucesso.')
        return super().form_valid(form)
