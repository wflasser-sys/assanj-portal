"""
Role-based permission decorators for view access control.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """
    Decorator to restrict view access to specific roles.
    Usage: @role_required(['admin', 'fetcher'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'User profile not found.')
                return redirect('accounts:login')
            
            if request.user.profile.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """Decorator to restrict view access to admin users only."""
    return role_required(['admin'])(view_func)


def fetcher_required(view_func):
    """Decorator to restrict view access to fetcher users only."""
    return role_required(['fetcher'])(view_func)


def developer_required(view_func):
    """Decorator to restrict view access to developer users only."""
    return role_required(['developer'])(view_func)
