from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from leads.models import Lead
from accounts.models import Role, UserProfile


class LeadsTests(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = User.objects.create_user(username='cold', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        role, _ = Role.objects.get_or_create(name='cold_caller')
        profile.roles.add(role)

    def test_add_lead_creates_record(self):
        self.c.login(username='cold', password='pass')
        resp = self.c.post(reverse('leads:add_lead'), {'business_name': 'B', 'phone_number': '123', 'category': 'Other'})
        # After add, redirect to cold caller dashboard
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Lead.objects.filter(business_name='B').exists())
