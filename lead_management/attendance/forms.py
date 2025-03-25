from django import forms
from django.utils import timezone
from .models import Attendance
from accounts.models import CustomUser

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ('user', 'date', 'time_in', 'time_out', 'status', 'notes')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_in': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'time_out': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PunchInForm(forms.Form):
    """Form for punching in"""
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )

class PunchOutForm(forms.Form):
    """Form for punching out"""
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )
