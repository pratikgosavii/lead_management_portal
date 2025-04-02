from django.db import models
from django.urls import reverse
from projects.models import Project
from accounts.models import CustomUser

class PaymentMethod(models.Model):
    """Model to define payment methods"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Payment(models.Model):
    """Model to store payment information"""

    STATUS_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'figma done'),
        ('Other_Company', 'Other_Company'),
        ('Cheque', 'Cheque'),
        ('Paypal', 'Paypal'),
    ]


    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    description = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    created_by = models.ForeignKey(
        CustomUser,
        related_name='created_payments',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Payment of {self.amount} for {self.project.name}"
    
    def get_absolute_url(self):
        return reverse('payment_detail', args=[str(self.id)])
