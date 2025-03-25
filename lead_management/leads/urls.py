from django.urls import path
from . import views

urlpatterns = [
    path('', views.LeadListView.as_view(), name='lead_list'),
    path('add/', views.LeadCreateView.as_view(), name='lead_add'),
    path('<int:pk>/', views.LeadDetailView.as_view(), name='lead_detail'),
    path('<int:pk>/edit/', views.LeadUpdateView.as_view(), name='lead_edit'),
    path('<int:pk>/delete/', views.LeadDeleteView.as_view(), name='lead_delete'),
    path('<int:pk>/assign/', views.LeadAssignView.as_view(), name='lead_assign'),
    path('my-leads/', views.MyLeadsView.as_view(), name='my_leads'),
    path('export/excel/', views.ExportLeadsExcelView.as_view(), name='lead_export_excel'),
    path('export/pdf/', views.ExportLeadsPDFView.as_view(), name='lead_export_pdf'),
]
