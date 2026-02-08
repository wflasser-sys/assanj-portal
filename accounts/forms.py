"""
Forms for user authentication and profile management.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile


class CustomLoginForm(AuthenticationForm):
    """Custom login form with basic styling."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile details."""
    class Meta:
        model = UserProfile
        fields = ['phone', 'city']
