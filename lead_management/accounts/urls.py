from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/<int:pk>/change-password/', AdminPasswordChangeView.as_view(), name='admin_password_change'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/add/', views.UserCreateView.as_view(), name='user_add'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
]
