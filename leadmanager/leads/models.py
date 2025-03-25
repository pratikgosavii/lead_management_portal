from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser


class LeadSource(models.Model):
    """
    Model to represent different sources of leads
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _('Lead Source')
        verbose_name_plural = _('Lead Sources')


class Lead(models.Model):
    """
    Model to represent sales leads
    """
    # Lead Status Choices
    NEW = 'new'
    CONTACTED = 'contacted'
    QUALIFIED = 'qualified'
    PROPOSAL = 'proposal'
    NEGOTIATION = 'negotiation'
    WON = 'won'
    LOST = 'lost'
    
    STATUS_CHOICES = [
        (NEW, 'New'),
        (CONTACTED, 'Contacted'),
        (QUALIFIED, 'Qualified'),
        (PROPOSAL, 'Proposal'),
        (NEGOTIATION, 'Negotiation'),
        (WON, 'Won'),
        (LOST, 'Lost'),
    ]
    
    # Lead Stage Choices
    STAGE_INITIAL = 'initial'
    STAGE_DISCOVERY = 'discovery'
    STAGE_EVALUATION = 'evaluation'
    STAGE_INTENT = 'intent'
    STAGE_PURCHASE = 'purchase'
    
    STAGE_CHOICES = [
        (STAGE_INITIAL, 'Initial Contact'),
        (STAGE_DISCOVERY, 'Discovery'),
        (STAGE_EVALUATION, 'Evaluation'),
        (STAGE_INTENT, 'Intent to Purchase'),
        (STAGE_PURCHASE, 'Purchase'),
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=200, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    
    # Lead Details
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=NEW)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=STAGE_INITIAL)
    
    # Estimated value
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    probability = models.IntegerField(default=0, help_text=_('Closing probability percentage'))
    
    # Assignment and tracking
    assigned_to = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        related_name='assigned_leads',
        null=True, 
        blank=True
    )
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        related_name='created_leads',
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    converted_to_client = models.BooleanField(default=False)
    
    # Next follow-up
    next_follow_up = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.company or 'No Company'}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_active(self):
        return self.status not in ['won', 'lost']
    
    @property
    def expected_value(self):
        """Calculate the expected value based on probability"""
        return (self.estimated_value * self.probability) / 100
    
    class Meta:
        verbose_name = _('Lead')
        verbose_name_plural = _('Leads')
        ordering = ['-created_at']


class Interaction(models.Model):
    """
    Model to track interactions with leads
    """
    CALL = 'call'
    EMAIL = 'email'
    MEETING = 'meeting'
    NOTE = 'note'
    
    INTERACTION_TYPE_CHOICES = [
        (CALL, 'Call'),
        (EMAIL, 'Email'),
        (MEETING, 'Meeting'),
        (NOTE, 'Note'),
    ]
    
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPE_CHOICES)
    date_time = models.DateTimeField()
    summary = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_interaction_type_display()} with {self.lead} on {self.date_time.strftime('%Y-%m-%d')}"
    
    class Meta:
        verbose_name = _('Interaction')
        verbose_name_plural = _('Interactions')
        ordering = ['-date_time']
