from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from django.urls import include, path
from transactions.views import DashboardView


def health_check(request):
    """Endpoint que força uma consulta real ao banco — usado pelo UptimeRobot
    para evitar que o Supabase pause o projeto por inatividade."""
    from participants.models import Participant
    count = Participant.objects.count()
    return JsonResponse({'status': 'ok', 'participants': count})


urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', DashboardView.as_view(), name='dashboard'),
    path('participants/', include('participants.urls')),
    path('users/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('transactions/', include('transactions.urls')),
    path('compliance/', include('compliance.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
