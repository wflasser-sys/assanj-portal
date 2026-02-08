"""
UserProfile model extended to support multiple roles per user.
Roles are defined in a separate Role model (multi-role allowed).
Admin is special and implies all roles.
"""

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Role(models.Model):
    """A simple Role model to support multi-role assignments."""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.display_name or self.name


class UserProfile(models.Model):
    """Extended user profile with multiple role assignments."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles = models.ManyToManyField(Role, blank=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        roles = ", ".join([r.name for r in self.roles.all()])
        return f"{self.user.username} - {roles or 'no-role'}"

    def get_role_display(self):
        """Return a readable list of role display names."""
        roles = [r.display_name or r.name for r in self.roles.all()]
        return ", ".join(roles) if roles else 'no-role'

    def has_role(self, role_name):
        """Return True if the user has the given role or is admin."""
        if self.roles.filter(name='admin').exists():
            return True
        return self.roles.filter(name=role_name).exists()
    def add_role(self, role_name):
        role, _ = Role.objects.get_or_create(name=role_name)
        self.roles.add(role)

    def remove_role(self, role_name):
        role = Role.objects.filter(name=role_name).first()
        if role:
            self.roles.remove(role)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create UserProfile when a new User is created and give default roles.

    Use get_or_create to avoid UNIQUE constraint errors when an inline or other
    process also creates the profile (common in admin add views).
    """
    if created:
        try:
            profile, created_profile = UserProfile.objects.get_or_create(
                user=instance,
                defaults={}
            )
            # Only add roles if this is a newly created profile
            if created_profile:
                # Default to 'cold_caller' role for created users unless superuser
                if instance.is_superuser:
                    admin_role, _ = Role.objects.get_or_create(name='admin')
                    profile.roles.add(admin_role)
                else:
                    default_role, _ = Role.objects.get_or_create(name='cold_caller')
                    profile.roles.add(default_role)
        except Exception:
            # If profile creation fails, it likely already exists
            pass


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Auto-save UserProfile when User is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
