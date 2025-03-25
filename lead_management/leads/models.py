from django.db import models
from django.urls import reverse
from accounts.models import CustomUser

class LeadSource(models.Model):
    """Model for tracking lead sources"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class LeadStatus(models.Model):
    """Model for tracking lead statuses"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_converted = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Lead statuses'
    
    def __str__(self):
        return self.name

class Lead(models.Model):
    """Model for tracking leads"""
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    source = models.ForeignKey(LeadSource, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey(LeadStatus, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey(
        CustomUser, 
        related_name='assigned_leads',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_by = models.ForeignKey(
        CustomUser,
        related_name='created_leads',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.company}" if self.company else self.name
    
    def get_absolute_url(self):
        return reverse('lead_detail', args=[str(self.id)])
    
    @property
    def is_converted(self):
        """Check if lead is converted"""
        return self.status.is_converted if self.status else False
