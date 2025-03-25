from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, date, timedelta
import pytz

from .models import Attendance
from .forms import AttendanceForm, PunchInForm, PunchOutForm
from accounts.models import CustomUser

# Set Indian Standard Time timezone
IST = pytz.timezone('Asia/Kolkata')

class AdminOrManagerRequiredMixin(UserPassesTestMixin):
    """Restrict access to admins or managers"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or
            self.request.user.role in ['admin', 'manager']
        )

class AttendanceListView(LoginRequiredMixin, AdminOrManagerRequiredMixin, ListView):
    """Display all attendance records"""
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Attendance.objects.all()
        
        # Search and filter options
        user_filter = self.request.GET.get('user', '')
        status_filter = self.request.GET.get('status', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        
        if user_filter:
            queryset = queryset.filter(user__id=user_filter)
            
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
            
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = CustomUser.objects.all()
        context['status_choices'] = dict(Attendance.STATUS_CHOICES)
        context['user_filter'] = self.request.GET.get('user', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        return context

class AttendanceDetailView(LoginRequiredMixin, DetailView):
    """Display attendance details"""
    model = Attendance
    template_name = 'attendance/attendance_detail.html'
    context_object_name = 'attendance'
    
    def dispatch(self, request, *args, **kwargs):
        # Allow users to see their own attendance
        attendance = self.get_object()
        if attendance.user != request.user and not (
            request.user.is_superuser or 
            request.user.role in ['admin', 'manager', 'team_leader']
        ):
            messages.error(request, "You don't have permission to view this attendance record.")
            return redirect('my_attendance')
            
        return super().dispatch(request, *args, **kwargs)

class AttendanceCreateView(LoginRequiredMixin, AdminOrManagerRequiredMixin, CreateView):
    """Create a new attendance record"""
    model = Attendance
    form_class = AttendanceForm
    template_name = 'attendance/attendance_form.html'
    success_url = reverse_lazy('attendance_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Attendance record created successfully.')
        return super().form_valid(form)

class AttendanceUpdateView(LoginRequiredMixin, AdminOrManagerRequiredMixin, UpdateView):
    """Update an existing attendance record"""
    model = Attendance
    form_class = AttendanceForm
    template_name = 'attendance/attendance_form.html'
    success_url = reverse_lazy('attendance_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Attendance record updated successfully.')
        return super().form_valid(form)

class AttendanceDeleteView(LoginRequiredMixin, AdminOrManagerRequiredMixin, DeleteView):
    """Delete an attendance record"""
    model = Attendance
    template_name = 'attendance/attendance_confirm_delete.html'
    success_url = reverse_lazy('attendance_list')
    
    def delete(self, request, *args, **kwargs):
        attendance = self.get_object()
        messages.success(request, f'Attendance record for {attendance.user.username} on {attendance.date} deleted successfully.')
        return super().delete(request, *args, **kwargs)

class PunchView(LoginRequiredMixin, TemplateView):
    """Handle punch in/out"""
    template_name = 'attendance/punch.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get current attendance status
        current_attendance = Attendance.get_current_attendance(self.request.user)
        context['current_attendance'] = current_attendance
        
        if current_attendance and current_attendance.is_ongoing:
            context['form'] = PunchOutForm()
            context['punch_type'] = 'out'
        else:
            context['form'] = PunchInForm()
            context['punch_type'] = 'in'
            
        # Get attendance history
        today = date.today()
        start_date = today - timedelta(days=7)
        context['attendance_history'] = Attendance.objects.filter(
            user=self.request.user,
            date__range=[start_date, today]
        ).order_by('-date')
        
        return context
    
    def post(self, request, *args, **kwargs):
        punch_type = request.POST.get('punch_type')
        
        if punch_type == 'in':
            form = PunchInForm(request.POST)
            if form.is_valid():
                notes = form.cleaned_data.get('notes')
                # Use IST time now
                ist_now = timezone.now().astimezone(IST)
                attendance = Attendance.punch_in(request.user, notes)
                # Display IST time in message
                messages.success(request, f'Punched in at {ist_now.strftime("%H:%M:%S")} IST')
        
        elif punch_type == 'out':
            form = PunchOutForm(request.POST)
            if form.is_valid():
                notes = form.cleaned_data.get('notes')
                # Use IST time now
                ist_now = timezone.now().astimezone(IST)
                attendance = Attendance.punch_out(request.user, notes)
                if attendance:
                    # Display IST time in message
                    messages.success(request, f'Punched out at {ist_now.strftime("%H:%M:%S")} IST')
                else:
                    messages.error(request, 'No active attendance found to punch out from.')
        
        return redirect('punch')

class MyAttendanceView(LoginRequiredMixin, ListView):
    """Display current user's attendance records"""
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Attendance.objects.filter(user=self.request.user)
        
        # Filter options
        status_filter = self.request.GET.get('status', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
            
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
            
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = dict(Attendance.STATUS_CHOICES)
        context['status_filter'] = self.request.GET.get('status', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['is_my_attendance'] = True
        
        # Calculate salary info
        if self.request.GET.get('show_salary', '') == 'true':
            # Get daily rate from user profile
            daily_rate = self.request.user.profile.daily_rate
            
            # Calculate days worked in current month
            today = date.today()
            first_day = date(today.year, today.month, 1)
            
            monthly_attendance = Attendance.objects.filter(
                user=self.request.user,
                date__gte=first_day,
                date__lte=today,
                status='present'
            )
            
            days_worked = monthly_attendance.count()
            context['days_worked'] = days_worked
            context['daily_rate'] = daily_rate
            context['monthly_salary'] = days_worked * daily_rate
            context['show_salary'] = True
        
        return context

class UserAttendanceView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Display attendance records for a specific user"""
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'attendances'
    paginate_by = 10
    
    def test_func(self):
        # Only admin, managers and team leaders can view other users' attendance
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or
            self.request.user.role in ['admin', 'manager', 'team_leader']
        )
    
    def dispatch(self, request, *args, **kwargs):
        self.selected_user = get_object_or_404(CustomUser, pk=kwargs['user_id'])
        
        # Team leaders can only view attendance for their team members
        if request.user.role == 'team_leader':
            team_members = CustomUser.objects.filter(
                Q(role='sales_rep') & 
                Q(profile__team_leader=request.user)
            )
            if self.selected_user not in team_members and self.selected_user != request.user:
                messages.error(request, "You don't have permission to view this user's attendance.")
                return redirect('attendance_list')
                
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Attendance.objects.filter(user=self.selected_user)
        
        # Filter options
        status_filter = self.request.GET.get('status', '')
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
            
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
            
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = dict(Attendance.STATUS_CHOICES)
        context['status_filter'] = self.request.GET.get('status', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['selected_user'] = self.selected_user
        
        # Calculate salary info if admin or manager
        if (self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']) and self.request.GET.get('show_salary', '') == 'true':
            # Get daily rate from user profile
            daily_rate = self.selected_user.profile.daily_rate
            
            # Calculate days worked in current month
            today = date.today()
            first_day = date(today.year, today.month, 1)
            
            monthly_attendance = Attendance.objects.filter(
                user=self.selected_user,
                date__gte=first_day,
                date__lte=today,
                status='present'
            )
            
            days_worked = monthly_attendance.count()
            context['days_worked'] = days_worked
            context['daily_rate'] = daily_rate
            context['monthly_salary'] = days_worked * daily_rate
            context['show_salary'] = True
        
        return context
