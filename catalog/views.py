from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView
from .forms import ProductForm, CounterpartyForm, ProductUnitConversionForm, ProductTransformationRuleForm
from .models import Product, Counterparty, ProductUnitConversion, ProductTransformationRule

class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_manager

class ProductListView(ManagerRequiredMixin, ListView):
    model = Product; template_name = 'catalog/product_list.html'; context_object_name = 'products'

class ProductCreateView(ManagerRequiredMixin, CreateView):
    model = Product; form_class = ProductForm; template_name = 'catalog/product_form.html'; success_url = reverse_lazy('product_list')
    def form_valid(self, form): messages.success(self.request, 'Produto criado com sucesso.'); return super().form_valid(form)

class ProductUpdateView(ManagerRequiredMixin, UpdateView):
    model = Product; form_class = ProductForm; template_name = 'catalog/product_form.html'; success_url = reverse_lazy('product_list')
    def form_valid(self, form): messages.success(self.request, 'Produto atualizado com sucesso.'); return super().form_valid(form)

class CounterpartyListView(ManagerRequiredMixin, ListView):
    model = Counterparty; template_name = 'catalog/counterparty_list.html'; context_object_name = 'counterparties'
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        qs = Counterparty.objects.select_related('participant').order_by('name')
        return qs.filter(participant__organization=org) if org else qs.none()

class CounterpartyCreateView(ManagerRequiredMixin, CreateView):
    model = Counterparty; form_class = CounterpartyForm; template_name = 'catalog/counterparty_form.html'; success_url = reverse_lazy('counterparty_list')
    def get_form(self, form_class=None):
        form = super().get_form(form_class); org = getattr(self.request.user, 'current_organization', None)
        if 'participant' in form.fields: form.fields['participant'].queryset = form.fields['participant'].queryset.filter(organization=org)
        return form
    def form_valid(self, form): messages.success(self.request, 'Cliente/fornecedor criado com sucesso.'); return super().form_valid(form)

class CounterpartyUpdateView(ManagerRequiredMixin, UpdateView):
    model = Counterparty; form_class = CounterpartyForm; template_name = 'catalog/counterparty_form.html'; success_url = reverse_lazy('counterparty_list')
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return Counterparty.objects.select_related('participant').filter(participant__organization=org) if org else Counterparty.objects.none()
    def get_form(self, form_class=None):
        form = super().get_form(form_class); org = getattr(self.request.user, 'current_organization', None)
        if 'participant' in form.fields: form.fields['participant'].queryset = form.fields['participant'].queryset.filter(organization=org)
        return form
    def form_valid(self, form): messages.success(self.request, 'Cliente/fornecedor atualizado com sucesso.'); return super().form_valid(form)

class ConversionListView(ManagerRequiredMixin, ListView):
    model = ProductUnitConversion; template_name = 'catalog/conversion_list.html'; context_object_name = 'conversions'; queryset = ProductUnitConversion.objects.select_related('product').order_by('product__name', 'from_unit', 'to_unit')

class ConversionCreateView(ManagerRequiredMixin, CreateView):
    model = ProductUnitConversion; form_class = ProductUnitConversionForm; template_name = 'catalog/conversion_form.html'; success_url = reverse_lazy('conversion_list')
    def form_valid(self, form): messages.success(self.request, 'Conversão de unidade criada com sucesso.'); return super().form_valid(form)

class ConversionUpdateView(ManagerRequiredMixin, UpdateView):
    model = ProductUnitConversion; form_class = ProductUnitConversionForm; template_name = 'catalog/conversion_form.html'; success_url = reverse_lazy('conversion_list')
    def form_valid(self, form): messages.success(self.request, 'Conversão de unidade atualizada com sucesso.'); return super().form_valid(form)

class TransformationRuleListView(ManagerRequiredMixin, ListView):
    model = ProductTransformationRule; template_name = 'catalog/transformation_rule_list.html'; context_object_name = 'rules'
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        qs = ProductTransformationRule.objects.select_related('participant', 'source_product', 'target_product').order_by('participant__trade_name', 'participant__legal_name', 'source_product__name', 'target_product__name')
        return qs.filter(participant__organization=org) if org else qs.none()

class TransformationRuleCreateView(ManagerRequiredMixin, CreateView):
    model = ProductTransformationRule; form_class = ProductTransformationRuleForm; template_name = 'catalog/transformation_rule_form.html'; success_url = reverse_lazy('transformation_rule_list')
    def get_form(self, form_class=None):
        form = super().get_form(form_class); org = getattr(self.request.user, 'current_organization', None)
        if 'participant' in form.fields: form.fields['participant'].queryset = form.fields['participant'].queryset.filter(organization=org)
        return form
    def form_valid(self, form): messages.success(self.request, 'Regra de transformação criada com sucesso.'); return super().form_valid(form)

class TransformationRuleUpdateView(ManagerRequiredMixin, UpdateView):
    model = ProductTransformationRule; form_class = ProductTransformationRuleForm; template_name = 'catalog/transformation_rule_form.html'; success_url = reverse_lazy('transformation_rule_list')
    def get_queryset(self):
        org = getattr(self.request.user, 'current_organization', None)
        return ProductTransformationRule.objects.select_related('participant', 'source_product', 'target_product').filter(participant__organization=org) if org else ProductTransformationRule.objects.none()
    def get_form(self, form_class=None):
        form = super().get_form(form_class); org = getattr(self.request.user, 'current_organization', None)
        if 'participant' in form.fields: form.fields['participant'].queryset = form.fields['participant'].queryset.filter(organization=org)
        return form
    def form_valid(self, form): messages.success(self.request, 'Regra de transformação atualizada com sucesso.'); return super().form_valid(form)
