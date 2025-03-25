from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

class CustomUser(AbstractUser):
    """Custom user model with role field"""
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('team_leader', 'Team Leader'),
        ('sales_rep', 'Sales Representative'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='sales_rep')
    
    def get_absolute_url(self):
        return reverse('user_detail', args=[str(self.id)])
    
    def __str__(self):
        return self.username

class UserProfile(models.Model):
    """Extended profile for users"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Profile for {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('user_detail', args=[str(self.user.id)])
