from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView,
    CounterpartyListView, CounterpartyCreateView, CounterpartyUpdateView,
    ConversionListView, ConversionCreateView, ConversionUpdateView,
    TransformationRuleListView, TransformationRuleCreateView, TransformationRuleUpdateView,
)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('counterparties/', CounterpartyListView.as_view(), name='counterparty_list'),
    path('counterparties/new/', CounterpartyCreateView.as_view(), name='counterparty_create'),
    path('counterparties/<int:pk>/edit/', CounterpartyUpdateView.as_view(), name='counterparty_update'),
    path('conversions/', ConversionListView.as_view(), name='conversion_list'),
    path('conversions/new/', ConversionCreateView.as_view(), name='conversion_create'),
    path('conversions/<int:pk>/edit/', ConversionUpdateView.as_view(), name='conversion_update'),
    path('transformation-rules/', TransformationRuleListView.as_view(), name='transformation_rule_list'),
    path('transformation-rules/new/', TransformationRuleCreateView.as_view(), name='transformation_rule_create'),
    path('transformation-rules/<int:pk>/edit/', TransformationRuleUpdateView.as_view(), name='transformation_rule_update'),
]
