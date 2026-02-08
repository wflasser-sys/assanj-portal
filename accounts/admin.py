"""
Admin configuration for UserProfile model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile on User admin page."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0  # Don't create extra blank forms


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline."""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_roles', 'is_staff')
    
    def get_roles(self, obj):
        try:
            if hasattr(obj, 'profile'):
                return ", ".join([r.name for r in obj.profile.roles.all()])
        except Exception:
            pass
        return '-'
    get_roles.short_description = 'Roles'
    
    def save_model(self, request, obj, form, change):
        """Ensure profile exists before saving."""
        super().save_model(request, obj, form, change)
        # Ensure profile exists
        if not hasattr(obj, 'profile'):
            try:
                UserProfile.objects.get_or_create(user=obj)
            except Exception:
                pass


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
