from django.urls import path
from . import views

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='payment_list'),
    path('add/', views.PaymentCreateView.as_view(), name='payment_add'),
    path('<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    path('<int:pk>/edit/', views.PaymentUpdateView.as_view(), name='payment_edit'),
    path('<int:pk>/delete/', views.PaymentDeleteView.as_view(), name='payment_delete'),
    path('project/<int:project_id>/', views.ProjectPaymentsView.as_view(), name='project_payments'),
]
