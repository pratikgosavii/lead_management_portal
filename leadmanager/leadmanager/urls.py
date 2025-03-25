"""
URL configuration for leadmanager project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('users/', include('users.urls')),
    path('leads/', include('leads.urls')),
    path('clients/', include('clients.urls')),
    path('projects/', include('projects.urls')),
    path('payments/', include('payments.urls')),
    path('attendance/', include('attendance.urls')),
    path('reports/', include('reports.urls')),
]
