"""
URL configuration for accounts app.
"""

from django.urls import path
from .views import CustomLoginView, logout_view, profile_view

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]
