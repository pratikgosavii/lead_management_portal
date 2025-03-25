from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import inlineformset_factory

from .models import Client, ClientContact
from .forms import ClientForm, ClientContactForm, ClientFromLeadForm
from leads.models import Lead
from users.models import CustomUser


class ClientListView(LoginRequiredMixin, ListView):
    """View to display all clients based on user role"""
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        queryset = Client.objects.all()
        
        # Apply role-based filtering
        if not user.is_admin:
            if user.is_manager:
                # Managers can see clients assigned to them or their team members
                queryset = queryset.filter(
                    Q(relationship_manager=user) | 
                    Q(relationship_manager__manager=user)
                )
            elif user.is_team_leader:
                # Team leaders can see clients assigned to them or their team members
                queryset = queryset.filter(
                    Q(relationship_manager=user) | 
                    Q(relationship_manager__manager=user)
                )
            else:
                # Sales reps can only see their own clients
                queryset = queryset.filter(relationship_manager=user)
        
        # Apply search filter if provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(contacts__name__icontains=search_query) |
                Q(contacts__email__icontains=search_query)
            ).distinct()
        
        # Apply status filter if provided
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Client.STATUS_CHOICES
        context['current_status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        # Add counts for dashboard
        client_counts = {}
        for status, label in Client.STATUS_CHOICES:
            client_counts[status] = self.get_queryset().filter(status=status).count()
        client_counts['total'] = self.get_queryset().count()
        context['client_counts'] = client_counts
        
        return context


class ClientDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View to display client details"""
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    
    def test_func(self):
        # Check if user has permission to view this client
        client = self.get_object()
        user = self.request.user
        
        if user.is_admin:
            return True
        if user.is_manager and (client.relationship_manager == user or client.relationship_manager.manager == user):
            return True
        if user.is_team_leader and (client.relationship_manager == user or client.relationship_manager.manager == user):
            return True
        if client.relationship_manager == user:
            return True
        
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contacts'] = self.object.contacts.all().order_by('-is_primary', 'name')
        
        # Add projects if available from the relationship
        from projects.models import Project
        context['projects'] = Project.objects.filter(client=self.object)
        
        # Add payments if available from the relationship
        from payments.models import Payment
        context['payments'] = Payment.objects.filter(project__client=self.object)
        
        # Calculate totals
        context['total_revenue'] = self.object.total_revenue
        context['pending_payments'] = self.object.pending_payments
        
        # Add contact form
        context['contact_form'] = ClientContactForm()
        
        return context


class ClientCreateView(LoginRequiredMixin, CreateView):
    """View to create a new client"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_url = reverse_lazy('client_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Set relationship manager to current user if not specified
        if not form.instance.relationship_manager:
            form.instance.relationship_manager = self.request.user
        
        messages.success(self.request, 'Client created successfully!')
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to update an existing client"""
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    
    def test_func(self):
        # Check if user has permission to edit this client
        client = self.get_object()
        user = self.request.user
        
        if user.is_admin:
            return True
        if user.is_manager and (client.relationship_manager == user or client.relationship_manager.manager == user):
            return True
        if user.is_team_leader and (client.relationship_manager == user or client.relationship_manager.manager == user):
            return True
        if client.relationship_manager == user:
            return True
        
        return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Client updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('client_detail', kwargs={'pk': self.object.pk})


@login_required
def add_client_contact(request, client_id):
    """View to add a new contact to a client"""
    client = get_object_or_404(Client, pk=client_id)
    
    # Check permission
    user = request.user
    if not user.is_admin and client.relationship_manager != user and (user.is_sales_rep or client.relationship_manager.manager != user):
        messages.error(request, "You don't have permission to add contacts to this client.")
        return redirect('client_detail', pk=client_id)
    
    if request.method == 'POST':
        form = ClientContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.client = client
            contact.save()
            messages.success(request, 'Contact added successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect('client_detail', pk=client_id)


@login_required
def create_client_from_lead(request, lead_id):
    """View to create a new client from a lead"""
    lead = get_object_or_404(Lead, pk=lead_id)
    
    # Check permission
    user = request.user
    if not user.is_admin and lead.assigned_to != user and (user.is_sales_rep or lead.assigned_to.manager != user):
        messages.error(request, "You don't have permission to convert this lead to a client.")
        return redirect('lead_detail', pk=lead_id)
    
    if request.method == 'POST':
        form = ClientFromLeadForm(request.POST, lead=lead, user=user)
        if form.is_valid():
            client = form.save(commit=False)
            client.lead_source = lead
            client.save()
            
            # Create a primary contact from lead's information
            ClientContact.objects.create(
                client=client,
                name=f"{lead.first_name} {lead.last_name}",
                position=lead.position,
                email=lead.email,
                phone=lead.phone,
                is_primary=True
            )
            
            messages.success(request, f"Lead successfully converted to client: {client.name}")
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientFromLeadForm(lead=lead, user=user)
    
    return render(request, 'clients/client_form.html', {
        'form': form,
        'lead': lead,
        'title': f"Convert Lead: {lead.full_name} to Client"
    })
