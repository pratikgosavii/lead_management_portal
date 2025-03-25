from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClientListView.as_view(), name='client_list'),
    path('add/', views.ClientCreateView.as_view(), name='client_add'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='client_edit'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
    path('convert-lead/<int:lead_id>/', views.ConvertLeadView.as_view(), name='convert_lead'),
    path('my-clients/', views.MyClientsView.as_view(), name='my_clients'),
]
