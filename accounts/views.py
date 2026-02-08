"""
Views for user authentication and profile management.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomLoginForm


class CustomLoginView(LoginView):
    """Custom login view with role-based redirect."""
    template_name = 'login.html'
    form_class = CustomLoginForm
    
    def get_success_url(self):
        return '/'


@login_required
def logout_view(request):
    """Logout view that redirects to login page."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Simple profile page showing user details and roles."""
    profile = getattr(request.user, 'profile', None)
    return render(request, 'accounts/profile.html', {'user_profile': profile})
