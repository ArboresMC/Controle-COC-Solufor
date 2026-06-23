from django.urls import path
from . import views

urlpatterns = [
    path('', views.ManejoDashboardView.as_view(), name='manejo_dashboard'),
    path('participante/', views.ManejoParticipantDashboardView.as_view(), name='manejo_participante_dashboard'),

    path('especies/', views.EspecieListView.as_view(), name='manejo_especie_list'),
    path('especies/nova/', views.EspecieCreateView.as_view(), name='manejo_especie_create'),
    path('especies/<int:pk>/editar/', views.EspecieUpdateView.as_view(), name='manejo_especie_update'),

    path('propriedades/', views.PropriedadeListView.as_view(), name='manejo_propriedade_list'),
    path('propriedades/nova/', views.PropriedadeCreateView.as_view(), name='manejo_propriedade_create'),
    path('propriedades/<int:pk>/editar/', views.PropriedadeUpdateView.as_view(), name='manejo_propriedade_update'),

    path('entradas/', views.InventarioEntradaListView.as_view(), name='manejo_entrada_list'),
    path('entradas/nova/', views.InventarioEntradaCreateView.as_view(), name='manejo_entrada_create'),

    path('saidas/', views.SaidaManejoListView.as_view(), name='manejo_saida_list'),
    path('saidas/nova/', views.SaidaManejoCreateView.as_view(), name='manejo_saida_create'),

    path('gestor/dados/', views.ManejoDataManagementView.as_view(), name='manejo_data_management'),
    path('gestor/dados/inativar/', views.ManejoDataDeactivateView.as_view(), name='manejo_data_deactivate'),
    path('gestor/dados/excluir/', views.ManejoDataDeleteView.as_view(), name='manejo_data_delete'),
    path('gestor/dados/excluir/unico/', views.ManejoDataDeleteSingleView.as_view(), name='manejo_data_delete_single'),

    path('importar/', views.ManejoImportWorkbookView.as_view(), name='manejo_import_workbook'),
    path('importar/modelo.xlsx', views.ManejoImportTemplateDownloadView.as_view(), name='manejo_import_template'),

    path('cadastro-lote/', views.ManejoCadastroImportView.as_view(), name='manejo_cadastro_import'),
    path('cadastro-lote/modelo.xlsx', views.ManejoCadastroTemplateDownloadView.as_view(), name='manejo_cadastro_template'),
]
