from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from leads.models import Lead
from projects.models import Project


class AdminLeadsOverviewTests(TestCase):
    def setUp(self):
        self.c = Client()
        # create admin user
        self.admin = User.objects.create_user(username='admin', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=self.admin)
        role, _ = Role.objects.get_or_create(name='admin')
        profile.roles.add(role)

        # create leads in different statuses
        Lead.objects.create(business_name='L1', phone_number='1', category='Other', status='new')
        Lead.objects.create(business_name='L2', phone_number='2', category='Other', status='contacted')
        Lead.objects.create(business_name='L3', phone_number='3', category='Other', status='meeting_booked')

    def test_admin_dashboard_includes_leads_groups(self):
        self.c.login(username='admin', password='pass')
        resp = self.c.get(reverse('admin_projects'))
        self.assertEqual(resp.status_code, 200)
        # Check that the leads groups are in context via template contains counts
        self.assertContains(resp, 'New')
        self.assertContains(resp, 'Contacted')
        self.assertContains(resp, 'Meetings')

    def test_create_project_uses_client_default_payouts(self):
        # Simulate fetcher creating a client (store defaults in session) and then creating a project
        fetcher = User.objects.create_user(username='fetcher', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=fetcher)
        role, _ = Role.objects.get_or_create(name='cold_caller')
        profile.roles.add(role)

        session = self.c.session
        session['new_client_data'] = {
            'full_name': 'Owner',
            'business_name': 'ClientX',
            'phone': '999',
            'email': 'a@b.com',
            'city': 'C',
            'business_category': 'Other',
            'fetcher_commission_amount': '1500.00',
            'developer_payout_amount': '5000.00',
            'agency_profit': '2000.00',
            'designer_payout_amount': '800.00',
            'seo_payout_amount': '600.00',
            'gbp_payout_amount': '400.00',
            'social_media_payout_amount': '300.00',
        }
        session.save()

        self.c.login(username='fetcher', password='pass')
        resp = self.c.post(reverse('projects:fetcher_add_project'), data={
            'project_type': 'custom',
            'website_type': 'business',
            'business_description': 'Test business description',
            'contact_info_phone': '999',
            'contact_info_email': 'a@b.com',
            'contact_info_address': 'addr',
            'deadline': '2099-12-31',
            'payment_status': 'not_paid',
        })
        # should create a project and redirect to fetcher_projects
        if resp.status_code != 302:
            # show errors for debugging
            content = resp.content.decode('utf-8') if hasattr(resp, 'content') else str(resp)
            self.fail(f"Expected redirect but got {resp.status_code}; response content:\n{content}")

        proj = Project.objects.filter(client__business_name='ClientX').first()
        self.assertIsNotNone(proj)
        # Payouts should have been applied
        self.assertEqual(float(proj.fetcher_commission_amount), 1500.00)
        self.assertEqual(float(proj.developer_payout_amount), 5000.00)
        self.assertEqual(float(proj.agency_profit), 2000.00)
        self.assertEqual(float(proj.designer_payout_amount), 800.00)
        self.assertEqual(float(proj.seo_payout_amount), 600.00)
        self.assertEqual(float(proj.gbp_payout_amount), 400.00)
        self.assertEqual(float(proj.social_media_payout_amount), 300.00)
    def test_sales_closer_cannot_set_payouts_via_create_client(self):
        # SalesCloser attempts to set payouts via CreateClientView -> CreateProjectView flow
        closer = User.objects.create_user(username='closer2', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=closer)
        role, _ = Role.objects.get_or_create(name='sales_closer')
        profile.roles.add(role)

        self.c.login(username='closer2', password='pass')
        # Post to create client with payout fields (maliciously included)
        resp = self.c.post(reverse('fetcher_add_client'), data={
            'full_name': 'SC Owner',
            'business_name': 'ClientSC2',
            'phone': '999',
            'email': 'sc2@example.com',
            'city': 'C',
            'business_category': 'Other',
            'fetcher_commission_amount': '1111.00',
            'developer_payout_amount': '2222.00',
        })
        # Should redirect to add project
        self.assertEqual(resp.status_code, 302)

        # Now create the project which should NOT have payouts applied
        resp = self.c.post(reverse('projects:fetcher_add_project'), data={
            'project_type': 'custom',
            'website_type': 'business',
            'business_description': 'SC created',
            'contact_info_phone': '999',
            'contact_info_email': 'sc2@example.com',
            'contact_info_address': 'addr',
            'deadline': '2099-12-31',
            'payment_status': 'not_paid',
        })
        self.assertEqual(resp.status_code, 302)
        proj = Project.objects.filter(client__business_name='ClientSC2').first()
        self.assertIsNotNone(proj)
        # Payouts should still be None
        self.assertIsNone(proj.fetcher_commission_amount)
        self.assertIsNone(proj.developer_payout_amount)
    def test_sales_closer_cannot_set_payouts_and_admin_assigns_and_finalizes(self):
        # Create sales closer and onboard a client+project
        closer = User.objects.create_user(username='closer', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=closer)
        role, _ = Role.objects.get_or_create(name='sales_closer')
        profile.roles.add(role)

        # Sales closer onboards client -> they should be redirected to complete project details (no client/project created yet)
        self.c.login(username='closer', password='pass')
        resp = self.c.post(reverse('leads:sales_closer_onboard'), data={
            'business_name': 'ClientSC',
            'phone': '999',
            'email': 'sc@example.com',
            'city': 'C'
        })
        self.assertEqual(resp.status_code, 302)
        # No project should exist yet; session should hold client data
        proj = Project.objects.filter(client__business_name='ClientSC').first()
        self.assertIsNone(proj)
        session = self.c.session
        self.assertIn('new_client_data', session)

        # Try to create an incomplete project (missing pages/services) - should fail validation
        resp = self.c.post(reverse('projects:fetcher_add_project'), data={
            'project_type': 'custom',
            'website_type': 'business',
            'business_description': 'SC created',
            'contact_info_phone': '999',
            'contact_info_email': 'sc@example.com',
            'contact_info_address': 'addr',
            'deadline': '2099-12-31',
            'payment_status': 'not_paid',
        })
        # Should not redirect due to validation errors
        self.assertNotEqual(resp.status_code, 302)

        # Now create a complete project with pages and services
        resp = self.c.post(reverse('fetcher_add_project'), data={
            'project_type': 'custom',
            'website_type': 'business',
            'business_description': 'SC created',
            'contact_info_phone': '999',
            'contact_info_email': 'sc@example.com',
            'contact_info_address': 'addr',
            'deadline': '2099-12-31',
            'payment_status': 'not_paid',
            'pages_required_text': 'Home\nAbout',
            'services_list_text': 'Web Design\nSEO'
        })
        self.assertEqual(resp.status_code, 302)
        proj = Project.objects.filter(client__business_name='ClientSC').first()
        self.assertIsNotNone(proj)
        # Payouts should NOT be set by sales closer
        self.assertIsNone(proj.developer_payout_amount)
        self.assertIsNone(proj.designer_payout_amount)

        # Now admin assigns the project and sets payouts
        admin = self.admin
        developer = User.objects.create_user(username='dev', password='pass')
        dev_profile, _ = UserProfile.objects.get_or_create(user=developer)
        dev_role, _ = Role.objects.get_or_create(name='developer')
        dev_profile.roles.add(dev_role)

        self.c.login(username='admin', password='pass')
        assign_url = reverse('admin_assign', kwargs={'pk': proj.pk})
        resp = self.c.post(assign_url, data={
            'assigned_to': str(developer.pk),
            'fetcher_commission_amount': '1000.00',
            'developer_payout_amount': '4000.00',
            'agency_profit': '1500.00',
            'designer_payout_amount': '500.00',
            'seo_payout_amount': '200.00',
            'gbp_payout_amount': '100.00',
            'social_media_payout_amount': '50.00',
        })
        # After assigning, admin should be redirected to project detail
        self.assertEqual(resp.status_code, 302)
        proj.refresh_from_db()
        self.assertEqual(float(proj.developer_payout_amount), 4000.00)
        self.assertEqual(float(proj.designer_payout_amount), 500.00)

        # Developer finalizes the project (mark completed)
        self.c.login(username='dev', password='pass')
        update_url = reverse('developer_update_status', kwargs={'pk': proj.pk})
        resp = self.c.post(update_url, data={'status': 'completed', 'developer_notes': 'Done'})
        self.assertEqual(resp.status_code, 302)
        proj.refresh_from_db()
        self.assertEqual(proj.status, 'completed')

        # Admin releases payment
        self.c.login(username='admin', password='pass')
        release_url = reverse('admin_payment_release', kwargs={'pk': proj.pk})
        resp = self.c.post(release_url)
        self.assertEqual(resp.status_code, 302)
        proj.refresh_from_db()
        self.assertTrue(proj.admin_payment_released)
        self.assertEqual(proj.status, 'payment_done')


class ExecutionEarningsTests(TestCase):
    def setUp(self):
        self.c = Client()
        # create a fetcher and a client
        self.fetcher = User.objects.create_user(username='fetcher_e', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=self.fetcher)
        role, _ = Role.objects.get_or_create(name='cold_caller')
        profile.roles.add(role)

        self.client_obj = None

        # Create execution users
        self.designer = User.objects.create_user(username='designer_user', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=self.designer)
        role, _ = Role.objects.get_or_create(name='designer')
        profile.roles.add(role)

        self.seo = User.objects.create_user(username='seo_user', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=self.seo)
        role, _ = Role.objects.get_or_create(name='seo')
        profile.roles.add(role)

        self.gbp = User.objects.create_user(username='gbp_user', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=self.gbp)
        role, _ = Role.objects.get_or_create(name='gbp')
        profile.roles.add(role)

        self.social = User.objects.create_user(username='social_user', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=self.social)
        role, _ = Role.objects.get_or_create(name='social_media')
        profile.roles.add(role)

    def create_project_with_payouts(self, completed=True, released=False, **payouts):
        from clients.models import Client
        from datetime import date
        client_obj = Client.objects.create(
            created_by=self.fetcher,
            full_name='Exec Owner',
            business_name='ExecClient',
            phone='999',
            email='a@b.com',
            city='C',
            business_category='Other'
        )
        proj = Project.objects.create(
            client=client_obj,
            created_by=self.fetcher,
            project_type='custom',
            website_type='business',
            business_description='Exec test',
            contact_info_phone='999',
            contact_info_email='a@b.com',
            contact_info_address='addr',
            deadline=date(2099, 12, 31),
            payment_status='paid_full',
            status='completed' if completed else 'in_progress',
            admin_payment_released=released,
            designer_payout_amount=payouts.get('designer', None),
            seo_payout_amount=payouts.get('seo', None),
            gbp_payout_amount=payouts.get('gbp', None),
            social_media_payout_amount=payouts.get('social', None),
        )
        # add team members if provided
        members = []
        if 'designer' in payouts:
            proj.assigned_team.add(self.designer)
        if 'seo' in payouts:
            proj.assigned_team.add(self.seo)
        if 'gbp' in payouts:
            proj.assigned_team.add(self.gbp)
        if 'social' in payouts:
            proj.assigned_team.add(self.social)
        proj.save()
        return proj

    def test_execution_roles_earnings_visible_after_release(self):
        proj = self.create_project_with_payouts(completed=True, released=True, designer=100.00, seo=200.00, gbp=300.00, social=400.00)

        # Designer
        self.c.login(username='designer_user', password='pass')
        resp = self.c.get(reverse('my_earnings'))
        self.assertEqual(resp.status_code, 200)
        self.assertAlmostEqual(resp.context['total'], 100.00)
        self.assertAlmostEqual(resp.context['pending'], 0)

        # SEO
        self.c.login(username='seo_user', password='pass')
        resp = self.c.get(reverse('my_earnings'))
        self.assertEqual(resp.status_code, 200)
        self.assertAlmostEqual(resp.context['total'], 200.00)

        # GBP
        self.c.login(username='gbp_user', password='pass')
        resp = self.c.get(reverse('my_earnings'))
        self.assertEqual(resp.status_code, 200)
        self.assertAlmostEqual(resp.context['total'], 300.00)

        # Social
        self.c.login(username='social_user', password='pass')
        resp = self.c.get(reverse('my_earnings'))
        self.assertEqual(resp.status_code, 200)
        self.assertAlmostEqual(resp.context['total'], 400.00)

    def test_execution_roles_pending_when_completed_but_not_released(self):
        proj = self.create_project_with_payouts(completed=True, released=False, designer=150.00, seo=250.00, gbp=350.00, social=450.00)

        # Designer pending
        self.c.login(username='designer_user', password='pass')
        resp = self.c.get(reverse('my_earnings'))
        self.assertEqual(resp.status_code, 200)
        self.assertAlmostEqual(resp.context['total'], 0)
        self.assertAlmostEqual(resp.context['pending'], 150.00)

        # SEO pending
        self.c.login(username='seo_user', password='pass')
        resp = self.c.get(reverse('my_earnings'))
        self.assertAlmostEqual(resp.context['pending'], 250.00)

