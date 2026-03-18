from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView,
    CounterpartyListView, CounterpartyCreateView, CounterpartyUpdateView,
)

urlpatterns = [
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('counterparties/', CounterpartyListView.as_view(), name='counterparty_list'),
    path('counterparties/new/', CounterpartyCreateView.as_view(), name='counterparty_create'),
    path('counterparties/<int:pk>/edit/', CounterpartyUpdateView.as_view(), name='counterparty_update'),
]
