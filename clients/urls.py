"""
URL configuration for clients app.
"""

from django.urls import path
from .views import CreateClientView, FetcherClientListView

urlpatterns = [
    path('add/', CreateClientView.as_view(), name='fetcher_add_client'),
    path('', FetcherClientListView.as_view(), name='fetcher_clients'),
]
