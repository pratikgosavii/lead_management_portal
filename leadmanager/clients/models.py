from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser
from leads.models import Lead


class Client(models.Model):
    """
    Model to represent clients who have been converted from leads
    """
    # Status Choices
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ON_HOLD = 'on_hold'
    
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (ON_HOLD, 'On Hold'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Business Details
    industry = models.CharField(max_length=100, blank=True, null=True)
    
    # Relationship Management
    relationship_manager = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        related_name='managed_clients',
        null=True, 
        blank=True
    )
    
    # Client Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    
    # Source Tracking
    lead_source = models.ForeignKey(
        Lead, 
        on_delete=models.SET_NULL, 
        related_name='converted_client',
        null=True, 
        blank=True,
        help_text=_('The lead that was converted to create this client')
    )
    
    # Notes and Timestamps
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def primary_contact(self):
        """Returns the primary contact for this client"""
        try:
            return self.contacts.get(is_primary=True)
        except ClientContact.DoesNotExist:
            return self.contacts.first()
    
    @property
    def projects_count(self):
        """Returns the number of projects associated with this client"""
        return self.projects.count()
    
    @property
    def total_revenue(self):
        """Returns the total revenue from all projects of this client"""
        from projects.models import Project
        return self.projects.aggregate(models.Sum('total_amount'))['total_amount__sum'] or 0
    
    @property
    def pending_payments(self):
        """Returns the total pending payments from all projects of this client"""
        from payments.models import Payment
        paid = Payment.objects.filter(project__client=self).aggregate(models.Sum('amount'))['amount__sum'] or 0
        return self.total_revenue - paid
    
    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
        ordering = ['-created_at']


class ClientContact(models.Model):
    """
    Model to represent contacts associated with a client
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False, help_text=_('Designate this as the primary contact for the client'))
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} ({self.client.name})"
    
    def save(self, *args, **kwargs):
        """Ensure only one primary contact per client"""
        if self.is_primary:
            # Set all other contacts of this client to not primary
            ClientContact.objects.filter(client=self.client).update(is_primary=False)
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('Client Contact')
        verbose_name_plural = _('Client Contacts')
        ordering = ['-is_primary', 'name']
