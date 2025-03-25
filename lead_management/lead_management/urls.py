
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('leads.urls')),
    path('accounts/', include('accounts.urls')),
    path('clients/', include('clients.urls')),
    path('reports/', include('reports.urls')),
    path('payments/', include('payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
