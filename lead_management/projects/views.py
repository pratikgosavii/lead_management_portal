from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q

from .models import Project, ProjectStatus
from .forms import ProjectForm
from clients.models import Client
from accounts.models import CustomUser

class AdminOrManagerRequiredMixin(UserPassesTestMixin):
    """Restrict access to admins or managers"""
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or
            self.request.user.role in ['admin', 'manager']
        )

class ProjectAccessMixin(UserPassesTestMixin):
    """Verify that the current user has access to the project"""
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
            
        # Admin and managers can access all projects
        if self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']:
            return True
            
        # Get the project object
        project_id = self.kwargs.get('pk')
        project = get_object_or_404(Project, pk=project_id)
        
        # Get the client and their associated lead's assigned_to
        client = project.client
        assigned_to = client.assigned_to
        
        if not assigned_to:
            # If no one is assigned, only admins/managers can access (already handled above)
            return False
            
        # Team leaders can access their own and their team members' projects
        if self.request.user.role == 'team_leader':
            team_members = CustomUser.objects.filter(
                Q(role='sales_rep') & 
                (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
            )
            return assigned_to in team_members
            
        # Sales reps can only access their own projects
        return assigned_to == self.request.user

class ProjectListView(LoginRequiredMixin, ListView):
    """Display all projects"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Project.objects.all()
        
        # Filter by role
        if not (self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']):
            # For team leaders and sales reps, filter projects by clients they manage
            clients = []
            
            if self.request.user.role == 'sales_rep':
                # Get clients from leads assigned to this user
                from leads.models import Lead
                leads = Lead.objects.filter(assigned_to=self.request.user)
                clients = Client.objects.filter(lead__in=leads)
            
            elif self.request.user.role == 'team_leader':
                # Get clients from leads assigned to team members
                from leads.models import Lead
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
                )
                leads = Lead.objects.filter(assigned_to__in=team_members)
                clients = Client.objects.filter(lead__in=leads)
            
            queryset = queryset.filter(client__in=clients)
            
        # Search query
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(client__name__icontains=search_query) |
                Q(client__company__icontains=search_query)
            )
            
        # Status filter
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status__id=status_filter)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = ProjectStatus.objects.all()
        context['active_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context

class ProjectDetailView(LoginRequiredMixin, ProjectAccessMixin, DetailView):
    """Display project details"""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add payments related to this project
        context['payments'] = self.object.payments.all().order_by('-payment_date')
        return context

class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Create a new project"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('project_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Project created successfully.')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # For non-admin/manager users, filter clients to those they have access to
        if not (self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']):
            from leads.models import Lead
            
            if self.request.user.role == 'sales_rep':
                leads = Lead.objects.filter(assigned_to=self.request.user)
                clients = Client.objects.filter(lead__in=leads)
            elif self.request.user.role == 'team_leader':
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
                )
                leads = Lead.objects.filter(assigned_to__in=team_members)
                clients = Client.objects.filter(lead__in=leads)
            
            form.fields['client'].queryset = clients
        
        return form

class ProjectUpdateView(LoginRequiredMixin, ProjectAccessMixin, UpdateView):
    """Update an existing project"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Project updated successfully.')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # For non-admin/manager users, filter clients to those they have access to
        if not (self.request.user.is_superuser or self.request.user.role in ['admin', 'manager']):
            from leads.models import Lead
            
            if self.request.user.role == 'sales_rep':
                leads = Lead.objects.filter(assigned_to=self.request.user)
                clients = Client.objects.filter(lead__in=leads)
            elif self.request.user.role == 'team_leader':
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=self.request.user) | Q(pk=self.request.user.pk))
                )
                leads = Lead.objects.filter(assigned_to__in=team_members)
                clients = Client.objects.filter(lead__in=leads)
            
            form.fields['client'].queryset = clients
        
        return form

class ProjectDeleteView(LoginRequiredMixin, AdminOrManagerRequiredMixin, DeleteView):
    """Delete a project"""
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    success_url = reverse_lazy('project_list')
    
    def delete(self, request, *args, **kwargs):
        project = self.get_object()
        messages.success(request, f'Project "{project}" deleted successfully.')
        return super().delete(request, *args, **kwargs)

class ClientProjectsView(LoginRequiredMixin, ListView):
    """Display projects for a specific client"""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        self.client = get_object_or_404(Client, pk=kwargs['client_id'])
        
        # Check permission to view this client's projects
        if not (request.user.is_superuser or request.user.role in ['admin', 'manager']):
            assigned_to = self.client.assigned_to
            
            if not assigned_to:
                messages.error(request, "You don't have permission to view this client's projects.")
                return redirect('client_list')
                
            if request.user.role == 'team_leader':
                team_members = CustomUser.objects.filter(
                    Q(role='sales_rep') & 
                    (Q(profile__team_leader=request.user) | Q(pk=request.user.pk))
                )
                if assigned_to not in team_members:
                    messages.error(request, "You don't have permission to view this client's projects.")
                    return redirect('client_list')
            elif assigned_to != request.user:
                messages.error(request, "You don't have permission to view this client's projects.")
                return redirect('client_list')
                
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Project.objects.filter(client=self.client)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = self.client
        context['statuses'] = ProjectStatus.objects.all()
        return context
