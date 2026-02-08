import os
import sys
import django
# Ensure project root is on sys.path so Django settings can be imported when running directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assanj_portal.settings')
try:
    django.setup()
except Exception as e:
    print('Error during django.setup():', e)
    raise

from django.contrib.auth.models import User

# Create a test user
username = 'test_user_for_integrity'
if not User.objects.filter(username=username).exists():
    u = User.objects.create(username=username, email='test@example.com')
    print('Created user', u.username)
    print('Profile exists?', hasattr(u, 'profile'))
else:
    print('User already exists, skipping')
