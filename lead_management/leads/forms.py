from django import forms
from .models import Lead, LeadSource, LeadStatus
from accounts.models import CustomUser

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ('name', 'company', 'phone', 'email', 'address', 'source', 'status', 'notes')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class LeadUpdateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ('name', 'company', 'phone', 'email', 'address', 'source', 'status', 'notes')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class LeadAssignForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(role__in=['manager', 'team_leader', 'sales_rep']),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Lead
        fields = ('assigned_to',)
