import os
import sys
import django
from django.utils import timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assanj_portal.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from accounts.models import Role, UserProfile
from leads.models import Lead
from projects.models import Project
from django.db import transaction

c = Client()

# Utility: create user with roles
def ensure_user(username, password='pass'):
    u, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.com'})
    if created:
        u.set_password(password)
        u.save()
    profile, _ = UserProfile.objects.get_or_create(user=u)
    return u


def add_role_to_user(user, role_name):
    role, _ = Role.objects.get_or_create(name=role_name, defaults={'display_name': role_name.replace('_', ' ').title()})
    user.profile.add_role(role)


print('Creating users...')
admin = ensure_user('int_admin')
add_role_to_user(admin, 'admin')

caller = ensure_user('int_caller')
add_role_to_user(caller, 'cold_caller')

closer = ensure_user('int_closer')
add_role_to_user(closer, 'sales_closer')

client_user = ensure_user('int_client')
add_role_to_user(client_user, 'client')

# Log in as cold caller and add a lead
print('\nTesting Cold Caller flow...')
logged_in = c.login(username='int_caller', password='pass')
if not logged_in:
    print('Login failed for cold caller (setting password now)')
    int_c = User.objects.get(username='int_caller')
    int_c.set_password('pass')
    int_c.save()
    c.login(username='int_caller', password='pass')

resp = c.post('/leads/cold-caller/add/', {
    'business_name': 'Test Business Inc',
    'phone_number': '+1234567890',
    'category': 'web',
})
print('Add lead response code:', resp.status_code)
lead = Lead.objects.filter(business_name='Test Business Inc').first()
print('Lead created:', bool(lead))

# Assign lead to sales closer
lead.assigned_sales_closer = closer
lead.save()
print('Assigned sales closer:', lead.assigned_sales_closer.username)

# Sales closer marks won -> creates project
print('\nTesting Sales Closer mark_won flow...')
# ensure closer has password
c.logout()
closer.set_password('pass')
closer.save()
assert c.login(username='int_closer', password='pass')
resp = c.get(f'/leads/sales-closer/mark-won/{lead.id}/')
print('Mark won response code:', resp.status_code)
lead.refresh_from_db()
print('Lead status after mark_won:', lead.status)
project = Project.objects.filter(lead=lead).first()
print('Project created:', bool(project), 'Project id:', project.id if project else None)

# Admin advances project through stages until completed
print('\nTesting Admin project stage advancement...')
admin.set_password('pass')
admin.save()
c.logout()
assert c.login(username='int_admin', password='pass')

if not project:
    print('No project found; aborting stage advancement test')
else:
    stages = [s[0] for s in Project.STAGE_CHOICES]
    print('Stages:', stages)
    for stage in stages[1:]:  # start from next stage
        resp = c.post(f'/projects/admin-panel/{project.id}/advance-stage/', {'next_stage': stage})
        print('Advance to', stage, 'status code', resp.status_code)
        project.refresh_from_db()
        print('Current stage:', project.current_stage)

print('\nIntegration test completed.')
