from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib import messages
from django.db.models import Q
from django.db import transaction

from .models import Client
from .forms import ClientForm
from leads.models import Lead, LeadStatus
from accounts.models import CustomUser

class AdminOrManagerRequiredMixin(UserPassesTestMixin):
    """Restrict access to admins or managers"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or
            self.request.user.role in ['admin', 'manager']
        )

class ClientAccessMixin(UserPassesTestMixin):
    """Verify that the current user has access to the client"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
            
        # Admin and managers can access all clients
        if self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']:
            return True
            
        # Get the client object
        client_id = self.kwargs.get('pk')
        client = get_object_or_404(Client, pk=client_id)
        
        # Check if the client is assigned to this user through their lead
        assigned_to = client.assigned_to
        
        if not assigned_to:
            # If no one is assigned, only admins/managers can access (already handled above)
            return False
            
        # Team leaders can access their own and their team members' clients
        if self.request.user.role == 'team_leader':
            team_members = CustomUser.objects.filter(
                Q(role='sales_rep') & 
                (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
            )
            return assigned_to in team_members
            
        # Sales reps can only access their own clients
        return assigned_to == self.request.user

class ClientListView(LoginRequiredMixin, ListView):
    """Display all clients"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Client.objects.all()
        
        # 
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class ClientDetailView(LoginRequiredMixin, ClientAccessMixin, DetailView):
    """Display client details"""
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'

class ClientCreateView(LoginRequiredMixin, CreateView):
    """Create a new client"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('client_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Client created successfully.')
        return super().form_valid(form)

class ClientUpdateView(LoginRequiredMixin, ClientAccessMixin, UpdateView):
    """Update an existing client"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Client updated successfully.')
        return super().form_valid(form)

class ClientDeleteView(LoginRequiredMixin, AdminOrManagerRequiredMixin, DeleteView):
    """Delete a client"""
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('client_list')
    
    def delete(self, request, *args, **kwargs):
        client = self.get_object()
        messages.success(request, f'Client "{client}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

class ConvertLeadView(LoginRequiredMixin, FormView):
    """Convert a lead to a client"""
    template_name = 'clients/client_form.html'
    form_class = ClientForm
    success_url = reverse_lazy('client_list')
    
    def dispatch(self, request, *args, **kwargs):
        self.lead = get_object_or_404(Lead, pk=kwargs['lead_id'])
        
        # Check if user has permission to convert this lead
        if not (request.user.is_superuser or request.user.role in ['admin', 'manager']):
            if request.user.role == 'team_leader':
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=request.user) | Q(pk=request.user.pk))
                )
                if self.lead.assigned_to not in team_members:
                    messages.error(request, "You don't have permission to convert this lead.")
                    return redirect('lead_list')
            elif self.lead.assigned_to != request.user:
                messages.error(request, "You don't have permission to convert this lead.")
                return redirect('lead_list')
                
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Prefill the form with lead information"""
        return {
            'name': self.lead.name,
            'company': self.lead.company,
            'phone': self.lead.phone,
            'email': self.lead.email,
            'address': self.lead.address,
            'lead': self.lead.id,
        }
    
    def form_valid(self, form):
        with transaction.atomic():
            # Save the client
            client = form.save(commit=False)
            client.created_by = self.request.user
            client.lead = self.lead
            client.save()
            
            # Update the lead status to converted
            converted_status = LeadStatus.objects.filter(is_converted=True).first()
            if converted_status:
                self.lead.status = converted_status
                self.lead.save()
            
            messages.success(self.request, f'Lead "{self.lead}" converted to client successfully.')
            return super().form_valid(form)

class MyClientsView(LoginRequiredMixin, ListView):
    """Display clients associated with the current user"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10
    
    def get_queryset(self):
        # Get all leads assigned to this user
        leads = Lead.objects.filter(assigned_to=self.request.user)
        return Client.objects.filter(lead__in=leads)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_my_clients'] = True
        return context
