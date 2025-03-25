from django import forms
from accounts.models import CustomUser
from leads.models import LeadStatus
from django.utils import timezone
from datetime import timedelta

class DateRangeForm(forms.Form):
    """Form for date range selection in reports"""
    PERIOD_CHOICES = (
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('this_quarter', 'This Quarter'),
        ('last_quarter', 'Last Quarter'),
        ('this_year', 'This Year'),
        ('last_year', 'Last Year'),
        ('custom', 'Custom Date Range'),
    )
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'period-select'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        today = timezone.now().date()
        
        if period == 'custom':
            if not start_date:
                self.add_error('start_date', 'Start date is required for custom range')
            if not end_date:
                self.add_error('end_date', 'End date is required for custom range')
            if start_date and end_date and start_date > end_date:
                self.add_error('end_date', 'End date cannot be before start date')
        else:
            # Set start_date and end_date based on period
            if period == 'today':
                start_date = today
                end_date = today
            elif period == 'yesterday':
                start_date = today - timedelta(days=1)
                end_date = today - timedelta(days=1)
            elif period == 'this_week':
                start_date = today - timedelta(days=today.weekday())
                end_date = today
            elif period == 'last_week':
                start_date = today - timedelta(days=today.weekday() + 7)
                end_date = today - timedelta(days=today.weekday() + 1)
            elif period == 'this_month':
                start_date = today.replace(day=1)
                end_date = today
            elif period == 'last_month':
                if today.month == 1:
                    start_date = today.replace(year=today.year-1, month=12, day=1)
                    end_date = today.replace(year=today.year-1, month=12, day=31)
                else:
                    start_date = today.replace(month=today.month-1, day=1)
                    if today.month == 3:
                        if today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0):
                            end_date = today.replace(month=2, day=29)
                        else:
                            end_date = today.replace(month=2, day=28)
                    elif today.month in [5, 7, 10, 12]:
                        end_date = today.replace(month=today.month-1, day=30)
                    else:
                        end_date = today.replace(month=today.month-1, day=31)
            elif period == 'this_quarter':
                current_quarter = (today.month - 1) // 3 + 1
                start_date = today.replace(month=3*current_quarter-2, day=1)
                end_date = today
            elif period == 'last_quarter':
                current_quarter = (today.month - 1) // 3 + 1
                last_quarter = current_quarter - 1 if current_quarter > 1 else 4
                if last_quarter == 4 and current_quarter == 1:
                    start_date = today.replace(year=today.year-1, month=10, day=1)
                    end_date = today.replace(year=today.year-1, month=12, day=31)
                else:
                    start_date = today.replace(month=3*last_quarter-2, day=1)
                    if last_quarter == 1:
                        end_date = today.replace(month=3, day=31)
                    elif last_quarter == 2:
                        end_date = today.replace(month=6, day=30)
                    elif last_quarter == 3:
                        end_date = today.replace(month=9, day=30)
                    else:
                        end_date = today.replace(month=12, day=31)
            elif period == 'this_year':
                start_date = today.replace(month=1, day=1)
                end_date = today
            elif period == 'last_year':
                start_date = today.replace(year=today.year-1, month=1, day=1)
                end_date = today.replace(year=today.year-1, month=12, day=31)
                
            cleaned_data['start_date'] = start_date
            cleaned_data['end_date'] = end_date
            
        return cleaned_data

class SalesReportForm(DateRangeForm):
    """Form for sales report with additional filters"""
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__in=['manager', 'team_leader', 'sales_rep']),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    group_by = forms.ChoiceField(
        choices=(
            ('day', 'Day'),
            ('week', 'Week'),
            ('month', 'Month'),
            ('user', 'User'),
        ),
        initial='month',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class LeadReportForm(DateRangeForm):
    """Form for lead report with additional filters"""
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__in=['manager', 'team_leader', 'sales_rep']),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ModelChoiceField(
        queryset=LeadStatus.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    group_by = forms.ChoiceField(
        choices=(
            ('day', 'Day'),
            ('week', 'Week'),
            ('month', 'Month'),
            ('status', 'Status'),
            ('user', 'User'),
        ),
        initial='status',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class PerformanceReportForm(DateRangeForm):
    """Form for performance report with additional filters"""
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__in=['manager', 'team_leader', 'sales_rep']),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
