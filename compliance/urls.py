from django.urls import path
from . import views

urlpatterns = [
    # Participante
    path('fechamentos/', views.MyClosingsView.as_view(), name='my_closings'),
    path('fechamentos/criar/', views.CreateClosingView.as_view(), name='create_closing'),
    path('fechamentos/<int:pk>/enviar/', views.SubmitClosingView.as_view(), name='submit_closing'),

    # Gestor
    path('gestor/fechamentos/', views.ManagerClosingDashboardView.as_view(), name='manager_closing_dashboard'),
    path('gestor/fechamentos/<int:pk>/', views.ClosingDetailView.as_view(), name='closing_detail'),
    path('gestor/fechamentos/<int:pk>/aprovar/', views.ApproveClosingView.as_view(), name='approve_closing'),
    path('gestor/fechamentos/<int:pk>/rejeitar/', views.RejectClosingView.as_view(), name='reject_closing'),
]
