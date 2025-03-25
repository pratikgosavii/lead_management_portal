from django import forms
from .models import Client, ClientContact
from users.models import CustomUser
from leads.models import Lead


class ClientForm(forms.ModelForm):
    """Form for creating and updating clients"""
    
    class Meta:
        model = Client
        fields = [
            'name', 'email', 'phone', 'website', 'address', 
            'industry', 'relationship_manager', 'status', 'notes'
        ]
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        
        # Limit relationship_manager choices based on user role
        if user:
            if user.is_admin:
                # Admin can assign to any user
                pass
            elif user.is_manager:
                # Managers can only assign to themselves or their team members
                self.fields['relationship_manager'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            elif user.is_team_leader:
                # Team leaders can only assign to themselves or their team members
                self.fields['relationship_manager'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            else:
                # Sales reps can only assign to themselves
                self.fields['relationship_manager'].queryset = CustomUser.objects.filter(pk=user.pk)


class ClientContactForm(forms.ModelForm):
    """Form for creating and updating client contacts"""
    
    class Meta:
        model = ClientContact
        fields = ['name', 'position', 'email', 'phone', 'is_primary', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'


class ClientFromLeadForm(forms.ModelForm):
    """Form for creating a client from a lead with pre-filled data"""
    
    class Meta:
        model = Client
        fields = [
            'name', 'email', 'phone', 'address', 
            'industry', 'relationship_manager', 'status', 'notes'
        ]
    
    def __init__(self, *args, **kwargs):
        lead = kwargs.pop('lead', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        
        # Limit relationship_manager choices based on user role
        if user:
            if user.is_admin:
                # Admin can assign to any user
                pass
            elif user.is_manager:
                # Managers can only assign to themselves or their team members
                self.fields['relationship_manager'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            elif user.is_team_leader:
                # Team leaders can only assign to themselves or their team members
                self.fields['relationship_manager'].queryset = CustomUser.objects.filter(
                    models.Q(pk=user.pk) | 
                    models.Q(manager=user)
                )
            else:
                # Sales reps can only assign to themselves
                self.fields['relationship_manager'].queryset = CustomUser.objects.filter(pk=user.pk)
        
        # Pre-fill data from lead if provided
        if lead:
            self.initial['name'] = lead.company if lead.company else f"{lead.first_name} {lead.last_name}"
            self.initial['email'] = lead.email
            self.initial['phone'] = lead.phone
            self.initial['address'] = lead.address
            self.initial['notes'] = lead.notes
            self.initial['relationship_manager'] = lead.assigned_to
