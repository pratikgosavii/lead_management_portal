from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, FormView
from django.db.models import Count, Sum, Avg, F, Q, DateField
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from datetime import datetime, timedelta, date
import calendar
import json

from .forms import DateRangeForm, SalesReportForm, LeadReportForm, PerformanceReportForm
from accounts.models import CustomUser
from leads.models import Lead, LeadStatus
from clients.models import Client
from projects.models import Project
from payments.models import Payment
from attendance.models import Attendance

class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard view"""
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Date ranges
        start_of_month = today.replace(day=1)
        last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
        last_month_end = start_of_month - timedelta(days=1)
        
        # User role-based filtering
        if user.is_superuser or user.role in ['admin', 'manager']:
            # Admin and managers see all data
            lead_filter = Q()
            client_filter = Q()
            payment_filter = Q()
        elif user.role == 'team_leader':
            # Team leaders see their own and team members' data
            team_members = CustomUser.objects.filter(
                Q(role='sales_rep') & 
                (Q(profile__team_leader=user) | Q(pk=user.pk))
            )
            lead_filter = Q(assigned_to__in=team_members)
            client_filter = Q(lead__assigned_to__in=team_members)
            payment_filter = Q(project__client__lead__assigned_to__in=team_members)
        else:
            # Sales reps see only their own data
            lead_filter = Q(assigned_to=user)
            client_filter = Q(lead__assigned_to=user)
            payment_filter = Q(project__client__lead__assigned_to=user)
        
        # Lead statistics
        context['total_leads'] = Lead.objects.filter(lead_filter).count()
        context['new_leads_month'] = Lead.objects.filter(
            lead_filter,
            created_at__gte=start_of_month
        ).count()
        
        # Get converted leads (clients)
        converted_status = LeadStatus.objects.filter(is_converted=True).first()
        if converted_status:
            context['converted_leads'] = Lead.objects.filter(
                lead_filter,
                status=converted_status
            ).count()
            
            try:
                context['conversion_rate'] = (
                    round((context['converted_leads'] / context['total_leads']) * 100, 2)
                    if context['total_leads'] > 0 else 0
                )
            except (ZeroDivisionError, TypeError):
                context['conversion_rate'] = 0
            
            context['this_month_conversions'] = Lead.objects.filter(
                lead_filter,
                status=converted_status,
                updated_at__gte=start_of_month
            ).count()
        else:
            context['converted_leads'] = 0
            context['conversion_rate'] = 0
            context['this_month_conversions'] = 0
        
        # Client statistics
        context['total_clients'] = Client.objects.filter(client_filter).count()
        context['new_clients_month'] = Client.objects.filter(
            client_filter,
            created_at__gte=start_of_month
        ).count()
        
        # Project statistics
        context['active_projects'] = Project.objects.filter(
            Q(client__in=Client.objects.filter(client_filter)) &
            ~Q(status__name__in=['Completed', 'Cancelled'])
        ).count()
        
        # Payment statistics with error handling
        try:
            context['total_revenue'] = Payment.objects.filter(payment_filter).aggregate(
                total=Sum('amount')
            )['total'] or 0
        except Exception:
            context['total_revenue'] = 0
        
        context['month_revenue'] = Payment.objects.filter(
            payment_filter,
            payment_date__gte=start_of_month
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        context['last_month_revenue'] = Payment.objects.filter(
            payment_filter,
            payment_date__gte=last_month_start,
            payment_date__lte=last_month_end
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Attendance statistics (personal for all users)
        try:
            context['today_attendance'] = Attendance.objects.get(
                user=user,
                date=today
            )
        except Attendance.DoesNotExist:
            context['today_attendance'] = None
        
        # Recent activities
        context['recent_leads'] = Lead.objects.filter(
            lead_filter
        ).order_by('-created_at')[:5]
        
        context['recent_clients'] = Client.objects.filter(
            client_filter
        ).order_by('-created_at')[:5]
        
        context['recent_payments'] = Payment.objects.filter(
            payment_filter
        ).order_by('-payment_date')[:5]
        
        # Lead status distribution
        lead_status_data = []
        for status in LeadStatus.objects.all():
            count = Lead.objects.filter(lead_filter, status=status).count()
            if count > 0:
                lead_status_data.append({
                    'status': status.name,
                    'count': count
                })
        context['lead_status_data'] = json.dumps(lead_status_data)
        
        # Monthly revenue chart data (last 6 months)
        revenue_data = []
        for i in range(5, -1, -1):
            month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            if i > 0:
                for _ in range(i):
                    month_start = (month_start - timedelta(days=1)).replace(day=1)
            
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            month_revenue = Payment.objects.filter(
                payment_filter,
                payment_date__gte=month_start,
                payment_date__lte=month_end
            ).aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            revenue_data.append({
                'month': month_start.strftime('%b %Y'),
                'revenue': float(month_revenue)
            })
        
        context['revenue_data'] = json.dumps(revenue_data)
        
        return context


class SalesReportView(LoginRequiredMixin, FormView):
    """Sales revenue report view"""
    template_name = 'reports/sales_report.html'
    form_class = SalesReportForm
    
    def get_initial(self):
        initial = super().get_initial()
        # Default to current month
        today = timezone.now().date()
        initial['period'] = 'this_month'
        initial['start_date'] = today.replace(day=1)
        initial['end_date'] = today
        initial['group_by'] = 'month'
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'GET':
            kwargs.update({
                'data': self.request.GET or None
            })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        form = context['form']
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            user = form.cleaned_data.get('user')
            group_by = form.cleaned_data.get('group_by', 'month')
            
            # User role-based filtering
            current_user = self.request.user
            if current_user.is_superuser or current_user.role in ['admin', 'manager']:
                # Admin and managers can see all data or filter by user
                if user:
                    payment_filter = Q(project__client__lead__assigned_to=user)
                else:
                    payment_filter = Q()
            elif current_user.role == 'team_leader':
                # Team leaders see their own and team members' data
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=current_user) | Q(pk=current_user.pk))
                )
                
                if user and user in team_members:
                    payment_filter = Q(project__client__lead__assigned_to=user)
                else:
                    payment_filter = Q(project__client__lead__assigned_to__in=team_members)
            else:
                # Sales reps see only their own data
                payment_filter = Q(project__client__lead__assigned_to=current_user)
            
            # Date range filter
            date_filter = Q(payment_date__gte=start_date, payment_date__lte=end_date)
            
            # Apply filters
            payments = Payment.objects.filter(payment_filter & date_filter)
            
            # Calculate total
            total_revenue = payments.aggregate(Sum('amount'))['amount__sum'] or 0
            
            # Group data based on selection
            if group_by == 'day':
                payments = payments.annotate(
                    period=TruncDay('payment_date')
                ).values('period').annotate(
                    total=Sum('amount')
                ).order_by('period')
                
                # Format for chart
                chart_data = [
                    {'date': payment['period'].strftime('%Y-%m-%d'), 'revenue': float(payment['total'])}
                    for payment in payments
                ]
                
            elif group_by == 'week':
                payments = payments.annotate(
                    period=TruncWeek('payment_date')
                ).values('period').annotate(
                    total=Sum('amount')
                ).order_by('period')
                
                # Format for chart
                chart_data = [
                    {'date': payment['period'].strftime('%Y-%m-%d'), 'revenue': float(payment['total'])}
                    for payment in payments
                ]
                
            elif group_by == 'month':
                payments = payments.annotate(
                    period=TruncMonth('payment_date')
                ).values('period').annotate(
                    total=Sum('amount')
                ).order_by('period')
                
                # Format for chart
                chart_data = [
                    {'date': payment['period'].strftime('%Y-%m'), 'revenue': float(payment['total'])}
                    for payment in payments
                ]
                
            elif group_by == 'user':
                payments = payments.values(
                    'project__client__lead__assigned_to__username',
                    'project__client__lead__assigned_to__first_name',
                    'project__client__lead__assigned_to__last_name'
                ).annotate(
                    total=Sum('amount')
                ).order_by('-total')
                
                # Format for chart
                chart_data = [
                    {
                        'user': (
                            f"{payment['project__client__lead__assigned_to__first_name']} "
                            f"{payment['project__client__lead__assigned_to__last_name']}"
                            if payment['project__client__lead__assigned_to__first_name']
                            else payment['project__client__lead__assigned_to__username']
                        ),
                        'revenue': float(payment['total'])
                    }
                    for payment in payments
                ]
            
            # Store results in context
            context['total_revenue'] = total_revenue
            context['payments'] = payments
            context['chart_data'] = json.dumps(chart_data)
            context['start_date'] = start_date
            context['end_date'] = end_date
            context['group_by'] = group_by
            
            # Get payment details for the detailed report
            payment_details = Payment.objects.filter(
                payment_filter & date_filter
            ).order_by('-payment_date')
            
            context['payment_details'] = payment_details
        
        return context
    
    def form_valid(self, form):
        # Just render the template with the form and results
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class LeadReportView(LoginRequiredMixin, FormView):
    """Lead analytics report view"""
    template_name = 'reports/sales_report.html'
    form_class = LeadReportForm
    
    def get_initial(self):
        initial = super().get_initial()
        # Default to current month
        today = timezone.now().date()
        initial['period'] = 'this_month'
        initial['start_date'] = today.replace(day=1)
        initial['end_date'] = today
        initial['group_by'] = 'status'
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'GET':
            kwargs.update({
                'data': self.request.GET or None
            })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        form = context['form']
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            user = form.cleaned_data.get('user')
            status = form.cleaned_data.get('status')
            group_by = form.cleaned_data.get('group_by', 'status')
            
            # User role-based filtering
            current_user = self.request.user
            if current_user.is_superuser or current_user.role in ['admin', 'manager']:
                # Admin and managers can see all data or filter by user
                if user:
                    lead_filter = Q(assigned_to=user)
                else:
                    lead_filter = Q()
            elif current_user.role == 'team_leader':
                # Team leaders see their own and team members' data
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=current_user) | Q(pk=current_user.pk))
                )
                
                if user and user in team_members:
                    lead_filter = Q(assigned_to=user)
                else:
                    lead_filter = Q(assigned_to__in=team_members)
            else:
                # Sales reps see only their own data
                lead_filter = Q(assigned_to=current_user)
            
            # Status filter
            if status:
                lead_filter &= Q(status=status)
            
            # Date range filter for created_at
            date_filter = Q(created_at__gte=start_date, created_at__lte=end_date)
            
            # Apply filters
            leads = Lead.objects.filter(lead_filter & date_filter)
            
            # Calculate total
            total_leads = leads.count()
            converted_status = LeadStatus.objects.filter(is_converted=True).first()
            converted_leads = leads.filter(status=converted_status).count() if converted_status else 0
            conversion_rate = round((converted_leads / total_leads) * 100, 2) if total_leads > 0 else 0
            
            # Group data based on selection
            if group_by == 'day':
                lead_data = leads.annotate(
                    period=TruncDay('created_at')
                ).values('period').annotate(
                    count=Count('id')
                ).order_by('period')
                
                # Format for chart
                chart_data = [
                    {'date': data['period'].strftime('%Y-%m-%d'), 'count': data['count']}
                    for data in lead_data
                ]
                
            elif group_by == 'week':
                lead_data = leads.annotate(
                    period=TruncWeek('created_at')
                ).values('period').annotate(
                    count=Count('id')
                ).order_by('period')
                
                # Format for chart
                chart_data = [
                    {'date': data['period'].strftime('%Y-%m-%d'), 'count': data['count']}
                    for data in lead_data
                ]
                
            elif group_by == 'month':
                lead_data = leads.annotate(
                    period=TruncMonth('created_at')
                ).values('period').annotate(
                    count=Count('id')
                ).order_by('period')
                
                # Format for chart
                chart_data = [
                    {'date': data['period'].strftime('%Y-%m'), 'count': data['count']}
                    for data in lead_data
                ]
                
            elif group_by == 'status':
                lead_data = leads.values(
                    'status__name'
                ).annotate(
                    count=Count('id')
                ).order_by('status__name')
                
                # Format for chart
                chart_data = [
                    {'status': data['status__name'] or 'None', 'count': data['count']}
                    for data in lead_data
                ]
                
            elif group_by == 'user':
                lead_data = leads.values(
                    'assigned_to__username',
                    'assigned_to__first_name',
                    'assigned_to__last_name'
                ).annotate(
                    count=Count('id')
                ).order_by('-count')
                
                # Format for chart
                chart_data = [
                    {
                        'user': (
                            f"{data['assigned_to__first_name']} {data['assigned_to__last_name']}"
                            if data['assigned_to__first_name']
                            else data['assigned_to__username']
                        ) if data['assigned_to__username'] else 'Unassigned',
                        'count': data['count']
                    }
                    for data in lead_data
                ]
            
            # Store results in context
            context['total_leads'] = total_leads
            context['converted_leads'] = converted_leads
            context['conversion_rate'] = conversion_rate
            context['lead_data'] = lead_data
            context['chart_data'] = json.dumps(chart_data)
            context['start_date'] = start_date
            context['end_date'] = end_date
            context['group_by'] = group_by
            context['is_lead_report'] = True
            
            # Get lead details for the detailed report
            lead_details = leads.order_by('-created_at')
            context['lead_details'] = lead_details
        
        return context
    
    def form_valid(self, form):
        # Just render the template with the form and results
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class PerformanceReportView(LoginRequiredMixin, FormView):
    """User performance analytics report view"""
    template_name = 'reports/performance_report.html'
    form_class = PerformanceReportForm
    
    def get_initial(self):
        initial = super().get_initial()
        # Default to current month
        today = timezone.now().date()
        initial['period'] = 'this_month'
        initial['start_date'] = today.replace(day=1)
        initial['end_date'] = today
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'GET':
            kwargs.update({
                'data': self.request.GET or None
            })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        form = context['form']
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            selected_user = form.cleaned_data.get('user')
            
            # User role-based filtering
            current_user = self.request.user
            if current_user.is_superuser or current_user.role in ['admin', 'manager']:
                # Admin and managers can see all data or filter by user
                if selected_user:
                    users = [selected_user]
                else:
                    users = CustomUser.objects.filter(role__in=['manager', 'team_leader', 'sales_rep'])
            elif current_user.role == 'team_leader':
                # Team leaders see their own and team members' data
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=current_user) | Q(pk=current_user.pk))
                )
                
                if selected_user and selected_user in team_members:
                    users = [selected_user]
                else:
                    users = team_members
            else:
                # Sales reps see only their own data
                users = [current_user]
            
            # Date ranges
            date_filter_leads = Q(created_at__date__gte=start_date, created_at__date__lte=end_date)
            date_filter_payments = Q(payment_date__gte=start_date, payment_date__lte=end_date)
            date_filter_attendance = Q(date__gte=start_date, date__lte=end_date)
            
            # Performance data
            performance_data = []
            
            for user in users:
                # Lead statistics
                lead_count = Lead.objects.filter(Q(assigned_to=user) & date_filter_leads).count()
                
                # Client conversion statistics
                converted_status = LeadStatus.objects.filter(is_converted=True).first()
                converted_leads = Lead.objects.filter(
                    Q(assigned_to=user) & date_filter_leads & Q(status=converted_status)
                ).count() if converted_status else 0
                
                conversion_rate = round((converted_leads / lead_count) * 100, 2) if lead_count > 0 else 0
                
                # Revenue statistics
                revenue = Payment.objects.filter(
                    Q(project__client__lead__assigned_to=user) & date_filter_payments
                ).aggregate(Sum('amount'))['amount__sum'] or 0
                
                # Attendance statistics
                attendance_days = Attendance.objects.filter(
                    Q(user=user) & date_filter_attendance & Q(status='present')
                ).count()
                
                # Calculate attendance hours by using time_in and time_out directly
                attendance_records = Attendance.objects.filter(
                    Q(user=user) & date_filter_attendance & Q(status='present')
                ).exclude(
                    Q(time_in=None) | Q(time_out=None)
                )
                
                # Calculate total hours manually
                attendance_hours = 0
                for record in attendance_records:
                    if record.time_in and record.time_out:
                        # Get duration in hours
                        duration = (record.time_out - record.time_in).total_seconds() / 3600
                        attendance_hours += duration
                
                # Add to performance data
                performance_data.append({
                    'user': user,
                    'lead_count': lead_count,
                    'converted_leads': converted_leads,
                    'conversion_rate': conversion_rate,
                    'revenue': revenue,
                    'attendance_days': attendance_days,
                    'attendance_hours': attendance_hours,
                    'revenue_per_lead': revenue / lead_count if lead_count > 0 else 0,
                    'daily_rate': user.profile.daily_rate,
                    'estimated_salary': user.profile.daily_rate * attendance_days
                })
            
            # Sort performance data by revenue
            performance_data.sort(key=lambda x: x['revenue'], reverse=True)
            
            # Prepare chart data
            user_labels = [
                f"{user['user'].first_name} {user['user'].last_name}" 
                if user['user'].first_name else user['user'].username
                for user in performance_data
            ]
            
            revenue_data = [float(user['revenue']) for user in performance_data]
            leads_data = [user['lead_count'] for user in performance_data]
            conversions_data = [user['converted_leads'] for user in performance_data]
            
            chart_data = {
                'labels': user_labels,
                'revenue': revenue_data,
                'leads': leads_data,
                'conversions': conversions_data
            }
            
            # Store results in context
            context['performance_data'] = performance_data
            context['chart_data'] = json.dumps(chart_data)
            context['start_date'] = start_date
            context['end_date'] = end_date
            
            # Additional context for detailed view if a single user is selected
            if selected_user:
                # Get lead details
                context['lead_details'] = Lead.objects.filter(
                    Q(assigned_to=selected_user) & date_filter_leads
                ).order_by('-created_at')
                
                # Get payment details
                context['payment_details'] = Payment.objects.filter(
                    Q(project__client__lead__assigned_to=selected_user) & date_filter_payments
                ).order_by('-payment_date')
                
                # Get attendance details
                context['attendance_details'] = Attendance.objects.filter(
                    Q(user=selected_user) & date_filter_attendance
                ).order_by('-date')
        
        return context
    
    def form_valid(self, form):
        # Just render the template with the form and results
        context = self.get_context_data(form=form)
        return self.render_to_response(context)


class AttendanceReportView(LoginRequiredMixin, FormView):
    """Attendance analytics report view"""
    template_name = 'reports/attendance_report.html'
    form_class = DateRangeForm
    
    def get_initial(self):
        initial = super().get_initial()
        # Default to current month
        today = timezone.now().date()
        initial['period'] = 'this_month'
        initial['start_date'] = today.replace(day=1)
        initial['end_date'] = today
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'GET':
            kwargs.update({
                'data': self.request.GET or None
            })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        form = context['form']
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # User role-based filtering
            current_user = self.request.user
            if current_user.is_superuser or current_user.role in ['admin', 'manager']:
                # Admin and managers can see all data
                users = CustomUser.objects.all()
            elif current_user.role == 'team_leader':
                # Team leaders see their own and team members' data
                users = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=current_user) | Q(pk=current_user.pk))
                )
            else:
                # Sales reps see only their own data
                users = CustomUser.objects.filter(pk=current_user.pk)
            
            # Date filter
            date_filter = Q(date__gte=start_date, date__lte=end_date)
            
            # Calculate attendance statistics for each user
            attendance_data = []
            
            for user in users:
                # Get attendance records for this user
                attendance_records = Attendance.objects.filter(
                    Q(user=user) & date_filter
                )
                
                # Count by status
                present_count = attendance_records.filter(status='present').count()
                absent_count = attendance_records.filter(status='absent').count()
                half_day_count = attendance_records.filter(status='half_day').count()
                leave_count = attendance_records.filter(status='leave').count()
                
                # Calculate total hours worked
                present_records = attendance_records.filter(status='present').exclude(
                    Q(time_in=None) | Q(time_out=None)
                )
                
                # Calculate total hours manually
                total_hours = 0
                for record in present_records:
                    if record.time_in and record.time_out:
                        # Get duration in hours
                        duration = (record.time_out - record.time_in).total_seconds() / 3600
                        total_hours += duration
                
                # Calculate average hours per day
                avg_hours = total_hours / present_count if present_count > 0 else 0
                
                # Calculate salary
                daily_rate = user.profile.daily_rate
                salary = daily_rate * present_count + (daily_rate * 0.5 * half_day_count)
                
                # Add to attendance data
                attendance_data.append({
                    'user': user,
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'half_day_count': half_day_count,
                    'leave_count': leave_count,
                    'total_days': (end_date - start_date).days + 1,
                    'attendance_percentage': round(present_count / ((end_date - start_date).days + 1) * 100, 2),
                    'total_hours': total_hours,
                    'avg_hours': round(avg_hours, 2),
                    'daily_rate': daily_rate,
                    'salary': salary
                })
            
            # Sort by attendance percentage (descending)
            attendance_data.sort(key=lambda x: x['attendance_percentage'], reverse=True)
            
            # Generate chart data
            user_labels = [
                f"{data['user'].first_name} {data['user'].last_name}" 
                if data['user'].first_name else data['user'].username
                for data in attendance_data
            ]
            
            present_data = [data['present_count'] for data in attendance_data]
            absent_data = [data['absent_count'] for data in attendance_data]
            half_day_data = [data['half_day_count'] for data in attendance_data]
            leave_data = [data['leave_count'] for data in attendance_data]
            
            chart_data = {
                'labels': user_labels,
                'present': present_data,
                'absent': absent_data,
                'half_day': half_day_data,
                'leave': leave_data
            }
            
            # Store results in context
            context['attendance_data'] = attendance_data
            context['chart_data'] = json.dumps(chart_data)
            context['start_date'] = start_date
            context['end_date'] = end_date
            
            # Calculate totals
            context['total_salary'] = sum(data['salary'] for data in attendance_data)
            context['total_days_worked'] = sum(data['present_count'] for data in attendance_data)
        
        return context
    
    def form_valid(self, form):
        # Just render the template with the form and results
        context = self.get_context_data(form=form)
        return self.render_to_response(context)
