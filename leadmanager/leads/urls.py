from django.urls import path
from . import views

urlpatterns = [
    path('', views.LeadListView.as_view(), name='lead_list'),
    path('<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('create/', views.LeadCreateView.as_view(), name='lead_create'),
    path('<int:pk>/update/', views.LeadUpdateView.as_view(), name='lead_update'),
    path('<int:lead_id>/add-interaction/', views.add_interaction, name='add_interaction'),
    path('<int:lead_id>/update-status/', views.update_lead_status, name='update_lead_status'),
    path('<int:lead_id>/assign/', views.assign_lead, name='assign_lead'),
    path('<int:lead_id>/convert/', views.convert_to_client, name='convert_to_client'),
]
