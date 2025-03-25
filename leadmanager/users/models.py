from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Custom User model with additional fields for role-based access control
    """
    ADMIN = 'admin'
    MANAGER = 'manager'
    TEAM_LEADER = 'team_leader'
    SALES_REP = 'sales_rep'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (TEAM_LEADER, 'Team Leader'),
        (SALES_REP, 'Sales Representative'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=SALES_REP,
        verbose_name=_('Role')
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    daily_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0,
        help_text=_('Daily salary amount for attendance-based calculations')
    )
    
    # Relationships
    manager = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='team_members',
        limit_choices_to={'role__in': [MANAGER, TEAM_LEADER]},
        help_text=_('Manager or team leader this user reports to')
    )
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN
    
    @property
    def is_manager(self):
        return self.role == self.MANAGER
    
    @property
    def is_team_leader(self):
        return self.role == self.TEAM_LEADER
    
    @property
    def is_sales_rep(self):
        return self.role == self.SALES_REP
    
    @property
    def can_manage_leads(self):
        return self.role in [self.ADMIN, self.MANAGER, self.TEAM_LEADER]
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
