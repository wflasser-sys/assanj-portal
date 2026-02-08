"""
Main URL configuration for Assanj Web Agency Workflow Portal.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Namespaced includes (templates use namespaced reverses)
    path('', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
    path('', include(('accounts.urls', 'accounts'), namespace='accounts')),
    # Keep fetcher prefixed clients include for backwards compatibility
    path('fetcher/clients/', include('clients.urls')),
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),
    path('leads/', include(('leads.urls', 'leads'), namespace='leads')),
    path('activity/', include(('activity.urls', 'activity'), namespace='activity')),
    path('clients/', include(('clients.urls', 'clients'), namespace='clients')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
