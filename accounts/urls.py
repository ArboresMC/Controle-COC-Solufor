from django.urls import path
from .views import UserListView, UserCreateView, UserUpdateView

urlpatterns = [
    path('', UserListView.as_view(), name='user_list'),
    path('new/', UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
]
