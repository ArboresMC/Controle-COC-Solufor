from django.urls import path
from .views import UserListView, UserCreateView, UserUpdateView, MeuPerfilView, AjudaView, TrocarSenhaView

urlpatterns = [
    path('', UserListView.as_view(), name='user_list'),
    path('new/', UserCreateView.as_view(), name='user_create'),
    path('<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('perfil/', MeuPerfilView.as_view(), name='meu_perfil'),
    path('ajuda/', AjudaView.as_view(), name='ajuda'),
    path('trocar-senha/', TrocarSenhaView.as_view(), name='trocar_senha'),
]
