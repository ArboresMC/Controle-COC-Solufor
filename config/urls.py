from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from transactions.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
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
