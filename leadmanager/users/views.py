from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views import View

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomUserPasswordChangeForm


def is_admin(user):
    """Check if user has admin role"""
    return user.is_authenticated and user.role == CustomUser.ADMIN


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class UserListView(ListView):
    """View to list all users (admin only)"""
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        role_filter = self.request.GET.get('role', '')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = CustomUser.ROLE_CHOICES
        context['current_role_filter'] = self.request.GET.get('role', '')
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class UserCreateView(CreateView):
    """View to create a new user (admin only)"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"User {form.instance.username} created successfully.")
        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class UserUpdateView(UpdateView):
    """View to update a user (admin only)"""
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"User {form.instance.username} updated successfully.")
        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin), name='dispatch')
class UserPasswordChangeView(View):
    """View to change a user's password (admin only)"""
    template_name = 'users/password_change.html'
    
    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = CustomUserPasswordChangeForm(user)
        return render(request, self.template_name, {'form': form, 'user': user})
    
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = CustomUserPasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Password for {user.username} changed successfully.")
            return redirect('user_list')
        return render(request, self.template_name, {'form': form, 'user': user})


@login_required
def profile_view(request):
    """View for users to see their own profile"""
    user = request.user
    return render(request, 'users/profile.html', {'user': user})
