from django.urls import path
from .views import ParticipantListView, ParticipantCreateView, ParticipantUpdateView

urlpatterns = [
    path('', ParticipantListView.as_view(), name='participant_list'),
    path('new/', ParticipantCreateView.as_view(), name='participant_create'),
    path('<int:pk>/edit/', ParticipantUpdateView.as_view(), name='participant_update'),
]
