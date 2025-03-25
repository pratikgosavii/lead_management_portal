from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models import CustomUser, UserProfile
from .forms import CustomUserCreationForm, CustomUserChangeForm, UserProfileForm

class AdminOrManagerRequiredMixin(UserPassesTestMixin):
    """Restrict access to admins or managers"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or
            self.request.user.role in ['admin', 'manager']
        )

class CustomLoginView(LoginView):
    """Custom login view"""
    template_name = 'registration/login.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, 'Your account is inactive. Please contact administrator.')
            return redirect('login')
        messages.success(self.request, 'Login successful.')
        return response

    def get_success_url(self):
        return self.success_url

class UserListView(LoginRequiredMixin, AdminOrManagerRequiredMixin, ListView):
    """List all users"""
    model = CustomUser
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        # Managers can only see team leaders and sales reps
        if self.request.user.role == 'manager':
            return CustomUser.objects.filter(role__in=['team_leader', 'sales_rep'])
        # Admins can see everyone
        return CustomUser.objects.all()

class UserDetailView(LoginRequiredMixin, AdminOrManagerRequiredMixin, DetailView):
    """View user details"""
    model = CustomUser
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_obj'

class UserCreateView(LoginRequiredMixin, AdminOrManagerRequiredMixin, CreateView):
    """Create a new user"""
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        messages.success(self.request, f'User {user.username} created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = UserProfileForm(self.request.POST)
        else:
            context['profile_form'] = UserProfileForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        profile_form = context['profile_form']

        with transaction.atomic():
            user = form.save()

            if profile_form.is_valid():
                profile = user.profile
                profile.phone_number = profile_form.cleaned_data.get('phone_number')
                profile.address = profile_form.cleaned_data.get('address')
                profile.daily_rate = profile_form.cleaned_data.get('daily_rate')
                profile.save()

            messages.success(self.request, f'User {user.username} created successfully.')
            return redirect(self.success_url)

        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, AdminOrManagerRequiredMixin, UpdateView):
    """Update an existing user"""
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = UserProfileForm(self.request.POST, instance=self.object.profile)
        else:
            context['profile_form'] = UserProfileForm(instance=self.object.profile)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        profile_form = context['profile_form']

        with transaction.atomic():
            user = form.save()

            if profile_form.is_valid():
                profile_form.save()

            messages.success(self.request, f'User {user.username} updated successfully.')
            return redirect(self.success_url)

        return super().form_valid(form)

class UserDeleteView(LoginRequiredMixin, AdminOrManagerRequiredMixin, DeleteView):
    """Delete a user"""
    model = CustomUser
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    context_object_name = 'user_obj'

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(request, f'User {user.username} deleted successfully.')
        return super().delete(request, *args, **kwargs)

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Change user password"""
    template_name = 'accounts/password_change_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully.')
        return super().form_valid(form)
@method_decorator(login_required, name='dispatch')
class AdminPasswordChangeView(AdminOrManagerRequiredMixin, View):
    """Admin view to change user passwords"""
    template_name = 'accounts/admin_password_change.html'

    def get(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = SetPasswordForm(user)
        return render(request, self.template_name, {'form': form, 'user_obj': user})

    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Password for {user.username} changed successfully.')
            return redirect('user_list')
        return render(request, self.template_name, {'form': form, 'user_obj': user})