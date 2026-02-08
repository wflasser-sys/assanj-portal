"""
Role-based permission mixins for class-based views.
Supports multi-role UserProfile using `profile.has_role(role_name)`.
Admin role short-circuits to allow access to everything.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin to restrict view access to specific roles.
    Set `allowed_roles` (list) in the view class.
    """
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not hasattr(request.user, 'profile'):
            messages.error(request, 'User profile not found.')
            return redirect('accounts:login')

        # Superusers are treated as admin
        profile = request.user.profile
        allowed = False
        for role in self.allowed_roles:
            if profile.has_role(role):
                allowed = True
                break

        if not allowed:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard:dashboard')

        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin to restrict view access to admin users only."""
    allowed_roles = ['admin']


class FetcherRequiredMixin(RoleRequiredMixin):
    """Mixin to restrict view access to users with the 'cold_caller' role."""
    allowed_roles = ['cold_caller']


class DeveloperRequiredMixin(RoleRequiredMixin):
    """Mixin to restrict view access to developer users only."""
    allowed_roles = ['developer']


class SalesCloserRequiredMixin(RoleRequiredMixin):
    """Mixin to restrict access to sales closers."""
    allowed_roles = ['sales_closer']


class ProjectExecutionMixin(RoleRequiredMixin):
    """Mixin for execution roles: designer, developer, seo, gbp."""
    allowed_roles = ['designer', 'developer', 'seo', 'gbp']


class ProjectManagerRequiredMixin(RoleRequiredMixin):
    """Mixin for admin/project_manager access."""
    allowed_roles = ['project_manager', 'admin']
