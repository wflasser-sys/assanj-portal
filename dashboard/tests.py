from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from clients.models import Client as BusinessClient
from projects.models import Project, ProjectUpdate
from activity.models import ActivityLog


class ClientDashboardTests(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = User.objects.create_user(username='clientuser', password='testpass')
        # create profile and client role
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        role, _ = Role.objects.get_or_create(name='client')
        profile.roles.add(role)

    def test_client_without_client_record_redirects(self):
        # Login and access /client/ — should redirect back to dashboard with message
        self.c.login(username='clientuser', password='testpass')
        resp = self.c.get(reverse('client_dashboard'))
        # Should redirect to dashboard because client record missing
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('dashboard'), resp['Location'])

    def test_client_with_linked_client_sees_projects(self):
        # Link a Client record and create a project
        business = BusinessClient.objects.create(created_by=self.user, full_name='Owner', business_name='Acme', phone='123', email='a@b.com', city='X', business_category='Other', user=self.user)
        proj = Project.objects.create(client=business, created_by=self.user, project_type='custom', website_type='business', pages_required='[]', services_list='[]', business_description='', contact_info_phone='123', contact_info_email='', contact_info_address='', deadline='2099-12-31', status='assigned')
        # Add updates and activity
        ProjectUpdate.objects.create(project=proj, user=self.user, message='Initial update')
        ActivityLog.objects.create(action='create', entity_type='project', entity_id=proj.id, performed_by=self.user, note='Created')

        self.c.login(username='clientuser', password='testpass')
        resp = self.c.get(reverse('client_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Acme')
        # Recent updates and activity should be in the rendered page
        self.assertContains(resp, 'Initial update')
        self.assertContains(resp, 'Created')
