from django.db import models
from django.urls import reverse
from clients.models import Client
from accounts.models import CustomUser

class ProjectStatus(models.Model):
    """Model to define project statuses"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name_plural = 'Project statuses'
    
    def __str__(self):
        return self.name

class Project(models.Model):
    """Model to store project information"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    status = models.ForeignKey(ProjectStatus, on_delete=models.SET_NULL, null=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser,
        related_name='created_projects',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.client.name}"
    
    def get_absolute_url(self):
        return reverse('project_detail', args=[str(self.id)])
    
    @property
    def total_payments(self):
        """Calculate total payments received for this project"""
        return self.payments.aggregate(models.Sum('amount'))['amount__sum'] or 0
    
    @property
    def payment_status(self):
        """Get payment status (paid, partially paid, unpaid)"""
        total_paid = self.total_payments
        if total_paid >= self.budget:
            return 'Paid'
        elif total_paid > 0:
            return 'Partially Paid'
        return 'Unpaid'
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to be paid"""
        return max(0, self.budget - self.total_payments)
