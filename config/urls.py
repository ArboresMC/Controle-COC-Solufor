from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def home_redirect(request):
    return redirect('/admin/')


def login_redirect(request):
    return redirect('/admin/login/?next=/admin/')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_redirect, name='login'),
    path('logout/', home_redirect, name='logout'),
    path('', home_redirect, name='dashboard'),
    path('participants/', include('participants.urls')),
    path('users/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('transactions/', include('transactions.urls')),
    path('compliance/', include('compliance.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
