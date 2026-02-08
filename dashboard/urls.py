"""
URL configuration for dashboard app.
"""

from django.urls import path
from .views import dashboard_router, fetcher_dashboard, my_projects
from . import views

urlpatterns = [
    path('', dashboard_router, name='dashboard'),
    path('fetcher/dashboard/', fetcher_dashboard, name='fetcher_dashboard'),
    path('cold-caller/', views.cold_caller_redirect, name='cold_caller_redirect'),
    path('execution/', views.execution_dashboard, name='execution_dashboard'),
    path('client/', views.client_dashboard, name='client_dashboard'),
    path('my-projects/', my_projects, name='my_projects'),
]
