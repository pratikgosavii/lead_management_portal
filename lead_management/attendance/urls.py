from django.urls import path
from . import views

urlpatterns = [
    path('', views.AttendanceListView.as_view(), name='attendance_list'),
    path('add/', views.AttendanceCreateView.as_view(), name='attendance_add'),
    path('<int:pk>/', views.AttendanceDetailView.as_view(), name='attendance_detail'),
    path('<int:pk>/edit/', views.AttendanceUpdateView.as_view(), name='attendance_edit'),
    path('<int:pk>/delete/', views.AttendanceDeleteView.as_view(), name='attendance_delete'),
    path('punch/', views.PunchView.as_view(), name='punch'),
    path('my-attendance/', views.MyAttendanceView.as_view(), name='my_attendance'),
    path('user/<int:user_id>/', views.UserAttendanceView.as_view(), name='user_attendance'),
]
