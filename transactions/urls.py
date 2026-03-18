from django.urls import path
from .views import (
    EntryCreateView, EntryListView, EntryUpdateView,
    SaleCreateView, SaleListView, SaleUpdateView,
    ManagerReviewEntryListView, ManagerReviewSaleListView,
)

urlpatterns = [
    path('entries/', EntryListView.as_view(), name='entry_list'),
    path('entries/new/', EntryCreateView.as_view(), name='entry_create'),
    path('entries/<int:pk>/edit/', EntryUpdateView.as_view(), name='entry_update'),
    path('sales/', SaleListView.as_view(), name='sale_list'),
    path('sales/new/', SaleCreateView.as_view(), name='sale_create'),
    path('sales/<int:pk>/edit/', SaleUpdateView.as_view(), name='sale_update'),
    path('manager/review/entries/', ManagerReviewEntryListView.as_view(), name='manager_review_entries'),
    path('manager/review/sales/', ManagerReviewSaleListView.as_view(), name='manager_review_sales'),
]
