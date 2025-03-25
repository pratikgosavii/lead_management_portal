from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('sales/', views.SalesReportView.as_view(), name='sales_report'),
    path('leads/', views.LeadReportView.as_view(), name='lead_report'),
    path('performance/', views.PerformanceReportView.as_view(), name='performance_report'),
    path('attendance/', views.AttendanceReportView.as_view(), name='attendance_report'),
]
