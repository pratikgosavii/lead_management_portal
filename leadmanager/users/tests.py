from django.test import TestCase
from django.urls import reverse
from .models import CustomUser


class UserModelTests(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            password='testpass123',
            role=CustomUser.ADMIN
        )
        self.manager_user = CustomUser.objects.create_user(
            username='manager',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        self.sales_user = CustomUser.objects.create_user(
            username='sales',
            password='testpass123',
            role=CustomUser.SALES_REP
        )

    def test_user_role_properties(self):
        """Test that role properties work correctly"""
        self.assertTrue(self.admin_user.is_admin)
        self.assertFalse(self.admin_user.is_manager)
        
        self.assertTrue(self.manager_user.is_manager)
        self.assertFalse(self.manager_user.is_admin)
        
        self.assertTrue(self.sales_user.is_sales_rep)
        self.assertFalse(self.sales_user.is_admin)

    def test_can_manage_leads_property(self):
        """Test that can_manage_leads property works correctly"""
        self.assertTrue(self.admin_user.can_manage_leads)
        self.assertTrue(self.manager_user.can_manage_leads)
        self.assertFalse(self.sales_user.can_manage_leads)
