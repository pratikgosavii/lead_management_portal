"""Lead management URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('leads/', include('leads.urls')),
    path('clients/', include('clients.urls')),
    path('projects/', include('projects.urls')),
    path('payments/', include('payments.urls')),
    path('attendance/', include('attendance.urls')),
    path('reports/', include('reports.urls')),
    path('', RedirectView.as_view(url='reports/dashboard/', permanent=False), name='home'),
]
