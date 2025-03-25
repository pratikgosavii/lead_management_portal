from django.test import TestCase
from django.urls import reverse
from .models import Lead, LeadSource
from users.models import CustomUser


class LeadModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            password='testpass123',
            role=CustomUser.SALES_REP
        )
        self.lead_source = LeadSource.objects.create(name='Website')
        self.lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            company='Test Company',
            email='john@example.com',
            phone='1234567890',
            status=Lead.NEW,
            stage=Lead.STAGE_INITIAL,
            source=self.lead_source,
            assigned_to=self.user,
            created_by=self.user,
            estimated_value=1000,
            probability=50
        )

    def test_lead_creation(self):
        self.assertEqual(self.lead.full_name, 'John Doe')
        self.assertTrue(self.lead.is_active)
        self.assertEqual(self.lead.expected_value, 500)  # 1000 * 50%


class LeadViewsTest(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            password='testpass123',
            role=CustomUser.ADMIN
        )
        self.sales_user = CustomUser.objects.create_user(
            username='salesrep',
            password='testpass123',
            role=CustomUser.SALES_REP
        )
        self.lead_source = LeadSource.objects.create(name='Website')
        self.lead = Lead.objects.create(
            first_name='John',
            last_name='Doe',
            company='Test Company',
            email='john@example.com',
            phone='1234567890',
            status=Lead.NEW,
            stage=Lead.STAGE_INITIAL,
            source=self.lead_source,
            assigned_to=self.sales_user,
            created_by=self.admin_user,
            estimated_value=1000,
            probability=50
        )

    def test_lead_list_view(self):
        # Login as admin
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('lead_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        
        # Login as sales rep
        self.client.login(username='salesrep', password='testpass123')
        response = self.client.get(reverse('lead_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')

    def test_lead_detail_view(self):
        # Login as admin
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('lead_detail', args=[self.lead.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        
        # Login as sales rep
        self.client.login(username='salesrep', password='testpass123')
        response = self.client.get(reverse('lead_detail', args=[self.lead.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')

    def test_lead_update_permission(self):
        # Test that a sales rep can update their own lead
        self.client.login(username='salesrep', password='testpass123')
        response = self.client.get(reverse('lead_update', args=[self.lead.id]))
        self.assertEqual(response.status_code, 200)
        
        # Create another sales rep
        other_sales_rep = CustomUser.objects.create_user(
            username='othersalesrep',
            password='testpass123',
            role=CustomUser.SALES_REP
        )
        
        # Assign lead to other sales rep
        self.lead.assigned_to = other_sales_rep
        self.lead.save()
        
        # Original sales rep should not be able to edit now
        response = self.client.get(reverse('lead_update', args=[self.lead.id]))
        self.assertEqual(response.status_code, 403)  # Forbidden
