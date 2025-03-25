from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q

from .models import Payment, PaymentMethod
from .forms import PaymentForm
from projects.models import Project
from accounts.models import CustomUser
from clients.models import Client

class AdminOrManagerRequiredMixin(UserPassesTestMixin):
    """Restrict access to admins or managers"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or
            self.request.user.role in ['admin', 'manager']
        )

class PaymentAccessMixin(UserPassesTestMixin):
    """Verify that the current user has access to the payment"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
            
        # Admin and managers can access all payments
        if self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']:
            return True
            
        # Get the payment object
        payment_id = self.kwargs.get('pk')
        payment = get_object_or_404(Payment, pk=payment_id)
        
        # Get the project, client and their associated lead's assigned_to
        project = payment.project
        client = project.client
        assigned_to = client.assigned_to
        
        if not assigned_to:
            # If no one is assigned, only admins/managers can access (already handled above)
            return False
            
        # Team leaders can access their own and their team members' payments
        if self.request.user.role == 'team_leader':
            team_members = CustomUser.objects.filter(
                Q(role='sales_rep') & 
                (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
            )
            return assigned_to in team_members
            
        # Sales reps can only access their own payments
        return assigned_to == self.request.user

class PaymentListView(LoginRequiredMixin, ListView):
    """Display all payments"""
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Payment.objects.all()
        
        # Filter by role
        if not (self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']):
            # For team leaders and sales reps, filter payments by projects they manage
            from leads.models import Lead
            
            if self.request.user.role == 'sales_rep':
                # Get clients from leads assigned to this user
                leads = Lead.objects.filter(assigned_to=self.request.user)
                clients = Client.objects.filter(lead__in=leads)
                projects = Project.objects.filter(client__in=clients)
            elif self.request.user.role == 'team_leader':
                # Get clients from leads assigned to team members
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
                )
                leads = Lead.objects.filter(assigned_to__in=team_members)
                clients = Client.objects.filter(lead__in=leads)
                projects = Project.objects.filter(client__in=clients)
            
            queryset = queryset.filter(project__in=projects)
            
        # Search query
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(project__name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(reference_number__icontains=search_query) |
                Q(project__client__name__icontains=search_query)
            )
            
        # Date filtering
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        
        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        return context

class PaymentDetailView(LoginRequiredMixin, PaymentAccessMixin, DetailView):
    """Display payment details"""
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'

class PaymentCreateView(LoginRequiredMixin, CreateView):
    """Create a new payment"""
    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'
    success_url = reverse_lazy('payment_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Payment recorded successfully.')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # For non-admin/manager users, filter projects to those they have access to
        if not (self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']):
            from leads.models import Lead
            
            if self.request.user.role == 'sales_rep':
                leads = Lead.objects.filter(assigned_to=self.request.user)
                clients = Client.objects.filter(lead__in=leads)
                projects = Project.objects.filter(client__in=clients)
            elif self.request.user.role == 'team_leader':
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
                )
                leads = Lead.objects.filter(assigned_to__in=team_members)
                clients = Client.objects.filter(lead__in=leads)
                projects = Project.objects.filter(client__in=clients)
            
            form.fields['project'].queryset = projects
        
        return form

class PaymentUpdateView(LoginRequiredMixin, PaymentAccessMixin, UpdateView):
    """Update an existing payment"""
    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment updated successfully.')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # For non-admin/manager users, filter projects to those they have access to
        if not (self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']):
            from leads.models import Lead
            
            if self.request.user.role == 'sales_rep':
                leads = Lead.objects.filter(assigned_to=self.request.user)
                clients = Client.objects.filter(lead__in=leads)
                projects = Project.objects.filter(client__in=clients)
            elif self.request.user.role == 'team_leader':
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
                )
                leads = Lead.objects.filter(assigned_to__in=team_members)
                clients = Client.objects.filter(lead__in=leads)
                projects = Project.objects.filter(client__in=clients)
            
            form.fields['project'].queryset = projects
        
        return form

class PaymentDeleteView(LoginRequiredMixin, AdminOrManagerRequiredMixin, DeleteView):
    """Delete a payment"""
    model = Payment
    template_name = 'payments/payment_confirm_delete.html'
    success_url = reverse_lazy('payment_list')
    
    def delete(self, request, *args, **kwargs):
        payment = self.get_object()
        messages.success(request, f'Payment for "{payment.project}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

class ProjectPaymentsView(LoginRequiredMixin, ListView):
    """Display payments for a specific project"""
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_id'])
        
        # Check permission to view this project's payments
        if not (request.user.is_superuser or request.user.role in ['admin', 'manager']):
            client = self.project.client
            assigned_to = client.assigned_to
            
            if not assigned_to:
                messages.error(request, "You don't have permission to view this project's payments.")
                return redirect('project_list')
                
            if request.user.role == 'team_leader':
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=request.user) | Q(pk=request.user.pk))
                )
                if assigned_to not in team_members:
                    messages.error(request, "You don't have permission to view this project's payments.")
                    return redirect('project_list')
            elif assigned_to != request.user:
                messages.error(request, "You don't have permission to view this project's payments.")
                return redirect('project_list')
                
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Payment.objects.filter(project=self.project)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['show_project_detail'] = False
        return context
