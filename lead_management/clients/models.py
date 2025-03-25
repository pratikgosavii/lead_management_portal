from django.db import models
from django.urls import reverse
from leads.models import Lead
from accounts.models import CustomUser

class Client(models.Model):
    """Model to store client information"""
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    lead = models.OneToOneField(
        Lead, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='converted_client'
    )
    created_by = models.ForeignKey(
        CustomUser,
        related_name='created_clients',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.company}" if self.company else self.name
    
    def get_absolute_url(self):
        return reverse('client_detail', args=[str(self.id)])
    
    @property
    def converted_from_lead(self):
        """Check if client was converted from lead"""
        return self.lead is not None
    
    @property
    def assigned_to(self):
        """Get the user assigned to this client (from lead)"""
        if self.lead:
            return self.lead.assigned_to
        return None
