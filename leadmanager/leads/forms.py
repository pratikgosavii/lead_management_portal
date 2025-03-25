from django import forms
from .models import Lead, LeadSource, Interaction
from users.models import CustomUser


class LeadForm(forms.ModelForm):
    """Form for creating and updating leads"""
    
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'company', 'position', 
            'email', 'phone', 'address', 'source', 'notes', 
            'status', 'stage', 'estimated_value', 'probability',
            'assigned_to', 'next_follow_up', 'converted_to_client'
        ]
        widgets = {
            'next_follow_up': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        
        # Limit assigned_to choices based on user role
        if user and not user.is_admin:
            if user.is_manager:
                # Managers can only assign to themselves or their team members
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            elif user.is_team_leader:
                # Team leaders can only assign to themselves or their team members
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            else:
                # Sales reps can only assign to themselves
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(pk=user.pk)


class LeadFilterForm(forms.Form):
    """Form for filtering leads"""
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + list(Lead.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    stage = forms.ChoiceField(
        choices=[('', 'All Stages')] + list(Lead.STAGE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    source = forms.ModelChoiceField(
        queryset=LeadSource.objects.all(),
        required=False,
        empty_label="All Sources",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    converted = forms.ChoiceField(
        choices=[
            ('', 'All Leads'),
            ('yes', 'Converted to Client'),
            ('no', 'Not Converted')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit assigned_to choices based on user role
        if user:
            if user.is_admin:
                # Admin can see all users
                pass
            elif user.is_manager:
                # Managers can only see themselves and their team members
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            elif user.is_team_leader:
                # Team leaders can only see themselves and their team members
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            else:
                # Sales reps can only see themselves
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(pk=user.pk)
                # Hide the field since there's only one option
                self.fields['assigned_to'].widget = forms.HiddenInput()


class InteractionForm(forms.ModelForm):
    """Form for recording interactions with leads"""
    
    class Meta:
        model = Interaction
        fields = ['interaction_type', 'date_time', 'summary', 'details']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'details': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class LeadStatusUpdateForm(forms.ModelForm):
    """Form for quickly updating lead status and stage"""
    
    class Meta:
        model = Lead
        fields = ['status', 'stage', 'probability', 'next_follow_up']
        widgets = {
            'next_follow_up': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class LeadAssignForm(forms.ModelForm):
    """Form for assigning leads to users"""
    
    class Meta:
        model = Lead
        fields = ['assigned_to']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        self.fields['assigned_to'].widget.attrs['class'] = 'form-select'
        
        # Limit assigned_to choices based on user role
        if user:
            if user.is_admin:
                # Admin can assign to any user
                pass
            elif user.is_manager:
                # Managers can only assign to themselves or their team members
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            elif user.is_team_leader:
                # Team leaders can only assign to themselves or their team members
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            else:
                # Sales reps can only assign to themselves
                self.fields['assigned_to'].queryset = CustomUser.objects.filter(pk=user.pk)
