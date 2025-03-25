from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect

from .models import Lead, LeadSource, Interaction
from .forms import LeadForm, LeadFilterForm, InteractionForm, LeadStatusUpdateForm, LeadAssignForm
from users.models import CustomUser


class LeadListView(LoginRequiredMixin, ListView):
    """View to display all leads based on user role and filters"""
    model = Lead
    template_name = 'leads/lead_list.html'
    context_object_name = 'leads'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.all()
        
        # Apply role-based filtering
        if not user.is_admin:
            if user.is_manager:
                # Managers can see leads assigned to them or their team members
                queryset = queryset.filter(
                    Q(assigned_to=user) | 
                    Q(assigned_to__manager=user)
                )
            elif user.is_team_leader:
                # Team leaders can see leads assigned to them or their team members
                queryset = queryset.filter(
                    Q(assigned_to=user) | 
                    Q(assigned_to__manager=user)
                )
            else:
                # Sales reps can only see their own leads
                queryset = queryset.filter(assigned_to=user)
        
        # Apply form filters
        form = LeadFilterForm(self.request.GET, user=user)
        if form.is_valid():
            # Filter by status
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(status=status)
            
            # Filter by stage
            stage = form.cleaned_data.get('stage')
            if stage:
                queryset = queryset.filter(stage=stage)
            
            # Filter by assigned_to
            assigned_to = form.cleaned_data.get('assigned_to')
            if assigned_to:
                queryset = queryset.filter(assigned_to=assigned_to)
            
            # Filter by source
            source = form.cleaned_data.get('source')
            if source:
                queryset = queryset.filter(source=source)
            
            # Filter by conversion status
            converted = form.cleaned_data.get('converted')
            if converted == 'yes':
                queryset = queryset.filter(converted_to_client=True)
            elif converted == 'no':
                queryset = queryset.filter(converted_to_client=False)
            
            # Filter by date range
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
        
        # Default ordering
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = LeadFilterForm(self.request.GET, user=self.request.user)
        
        # Add counts for the dashboard
        user = self.request.user
        if user.is_admin:
            base_queryset = Lead.objects.all()
        elif user.is_manager or user.is_team_leader:
            base_queryset = Lead.objects.filter(
                Q(assigned_to=user) | 
                Q(assigned_to__manager=user)
            )
        else:
            base_queryset = Lead.objects.filter(assigned_to=user)
        
        context['total_leads'] = base_queryset.count()
        context['new_leads'] = base_queryset.filter(status='new').count()
        context['contacted_leads'] = base_queryset.filter(status='contacted').count()
        context['qualified_leads'] = base_queryset.filter(status='qualified').count()
        context['won_leads'] = base_queryset.filter(status='won').count()
        context['lost_leads'] = base_queryset.filter(status='lost').count()
        
        # Follow-ups due today
        today_min = timezone.now().replace(hour=0, minute=0, second=0)
        today_max = timezone.now().replace(hour=23, minute=59, second=59)
        context['followups_today'] = base_queryset.filter(
            next_follow_up__gte=today_min,
            next_follow_up__lte=today_max
        ).count()
        
        return context


class LeadDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View to display lead details"""
    model = Lead
    template_name = 'leads/lead_detail.html'
    context_object_name = 'lead'
    
    def test_func(self):
        # Check if user has permission to view this lead
        lead = self.get_object()
        user = self.request.user
        
        if user.is_admin:
            return True
        if user.is_manager and (lead.assigned_to == user or lead.assigned_to.manager == user):
            return True
        if user.is_team_leader and (lead.assigned_to == user or lead.assigned_to.manager == user):
            return True
        if lead.assigned_to == user:
            return True
        
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add interaction form to context
        context['interaction_form'] = InteractionForm()
        
        # Add status update form to context
        context['status_form'] = LeadStatusUpdateForm(instance=self.object)
        
        # Add interactions to context
        context['interactions'] = self.object.interactions.all().order_by('-date_time')
        
        return context


class LeadCreateView(LoginRequiredMixin, CreateView):
    """View to create a new lead"""
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'
    success_url = reverse_lazy('lead_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        
        # If not specified, assign to the current user
        if not form.instance.assigned_to:
            form.instance.assigned_to = self.request.user
        
        messages.success(self.request, 'Lead created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('lead_detail', kwargs={'pk': self.object.pk})


class LeadUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View to update an existing lead"""
    model = Lead
    form_class = LeadForm
    template_name = 'leads/lead_form.html'
    
    def test_func(self):
        # Check if user has permission to edit this lead
        lead = self.get_object()
        user = self.request.user
        
        if user.is_admin:
            return True
        if user.is_manager and (lead.assigned_to == user or lead.assigned_to.manager == user):
            return True
        if user.is_team_leader and (lead.assigned_to == user or lead.assigned_to.manager == user):
            return True
        if lead.assigned_to == user:
            return True
        
        return False
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Lead updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('lead_detail', kwargs={'pk': self.object.pk})


@login_required
def add_interaction(request, lead_id):
    """View to add a new interaction to a lead"""
    lead = get_object_or_404(Lead, pk=lead_id)
    
    # Check permission
    user = request.user
    if not user.is_admin and lead.assigned_to != user and (user.is_sales_rep or lead.assigned_to.manager != user):
        messages.error(request, "You don't have permission to add interactions to this lead.")
        return redirect('lead_detail', pk=lead_id)
    
    if request.method == 'POST':
        form = InteractionForm(request.POST)
        if form.is_valid():
            interaction = form.save(commit=False)
            interaction.lead = lead
            interaction.created_by = request.user
            interaction.save()
            messages.success(request, 'Interaction added successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect('lead_detail', pk=lead_id)


@login_required
def update_lead_status(request, lead_id):
    """View to update a lead's status and stage"""
    lead = get_object_or_404(Lead, pk=lead_id)
    
    # Check permission
    user = request.user
    if not user.is_admin and lead.assigned_to != user and (user.is_sales_rep or lead.assigned_to.manager != user):
        messages.error(request, "You don't have permission to update this lead's status.")
        return redirect('lead_detail', pk=lead_id)
    
    if request.method == 'POST':
        form = LeadStatusUpdateForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            
            # Record this status change as an interaction
            status_text = dict(Lead.STATUS_CHOICES)[form.cleaned_data['status']]
            stage_text = dict(Lead.STAGE_CHOICES)[form.cleaned_data['stage']]
            Interaction.objects.create(
                lead=lead,
                interaction_type=Interaction.NOTE,
                date_time=timezone.now(),
                summary=f"Status updated to {status_text} / {stage_text}",
                details=f"Status changed to {status_text}\nStage changed to {stage_text}\nProbability updated to {form.cleaned_data['probability']}%",
                created_by=request.user
            )
            
            messages.success(request, 'Lead status updated successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect('lead_detail', pk=lead_id)


@login_required
def assign_lead(request, lead_id):
    """View to assign a lead to a user"""
    lead = get_object_or_404(Lead, pk=lead_id)
    
    # Check permission
    user = request.user
    if not user.can_manage_leads and lead.assigned_to != user:
        messages.error(request, "You don't have permission to assign this lead.")
        return redirect('lead_detail', pk=lead_id)
    
    if request.method == 'POST':
        form = LeadAssignForm(request.POST, instance=lead, user=user)
        if form.is_valid():
            previous_assignee = lead.assigned_to
            form.save()
            
            # Record this assignment as an interaction
            new_assignee = form.cleaned_data['assigned_to']
            Interaction.objects.create(
                lead=lead,
                interaction_type=Interaction.NOTE,
                date_time=timezone.now(),
                summary=f"Lead assigned to {new_assignee.get_full_name()}",
                details=f"Lead reassigned from {previous_assignee.get_full_name() if previous_assignee else 'Unassigned'} to {new_assignee.get_full_name()}",
                created_by=request.user
            )
            
            messages.success(request, f'Lead assigned to {new_assignee.get_full_name()} successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect('lead_detail', pk=lead_id)


@login_required
def convert_to_client(request, lead_id):
    """View to convert a lead to a client"""
    lead = get_object_or_404(Lead, pk=lead_id)
    
    # Check permission
    user = request.user
    if not user.is_admin and lead.assigned_to != user and (user.is_sales_rep or lead.assigned_to.manager != user):
        messages.error(request, "You don't have permission to convert this lead.")
        return redirect('lead_detail', pk=lead_id)
    
    # Update lead status
    lead.status = Lead.WON
    lead.stage = Lead.STAGE_PURCHASE
    lead.converted_to_client = True
    lead.save()
    
    # Record this conversion as an interaction
    Interaction.objects.create(
        lead=lead,
        interaction_type=Interaction.NOTE,
        date_time=timezone.now(),
        summary="Lead converted to client",
        details="Lead has been successfully converted to a client.",
        created_by=request.user
    )
    
    # Redirect to create client form, pre-populated with lead data
    return redirect(reverse('client_create_from_lead', kwargs={'lead_id': lead_id}))
