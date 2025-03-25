from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClientListView.as_view(), name='client_list'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('create/', views.ClientCreateView.as_view(), name='client_create'),
    path('<int:pk>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('<int:client_id>/add-contact/', views.add_client_contact, name='add_client_contact'),
    path('create-from-lead/<int:lead_id>/', views.create_client_from_lead, name='client_create_from_lead'),
]
