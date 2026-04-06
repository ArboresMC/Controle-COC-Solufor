from django.urls import path
from .views import (
    EntryCreateView, EntryListView, EntryUpdateView,
    SaleCreateView, SaleListView, SaleUpdateView,
    TransformationCreateView, TransformationListView, TransformationUpdateView,
    DocumentCenterView,
)

urlpatterns = [
    path('entries/', EntryListView.as_view(), name='entry_list'),
    path('entries/new/', EntryCreateView.as_view(), name='entry_create'),
    path('entries/<int:pk>/edit/', EntryUpdateView.as_view(), name='entry_update'),
    path('sales/', SaleListView.as_view(), name='sale_list'),
    path('sales/new/', SaleCreateView.as_view(), name='sale_create'),
    path('sales/<int:pk>/edit/', SaleUpdateView.as_view(), name='sale_update'),
    path('transformations/', TransformationListView.as_view(), name='transformation_list'),
    path('transformations/new/', TransformationCreateView.as_view(), name='transformation_create'),
    path('transformations/<int:pk>/edit/', TransformationUpdateView.as_view(), name='transformation_update'),
    path('documents/', DocumentCenterView.as_view(), name='document_center'),
]
