from django import template

register = template.Library()


@register.filter(name='has_role')
def has_role(obj, role_name):
    """Template filter: returns True if given User or UserProfile has the role."""
    try:
        # If a User instance is passed
        from django.contrib.auth.models import User
        if isinstance(obj, User):
            profile = getattr(obj, 'profile', None)
            if profile:
                return profile.has_role(role_name)
            return False
        # If a UserProfile is passed
        return obj.has_role(role_name)
    except Exception:
        return False


@register.filter(name='filter_role')
def filter_role(users, role_name):
    """Return a queryset/list of users filtered by role name.

    Works with QuerySet (uses ORM filter) and with plain iterables (falls back to python filtering).
    """
    try:
        # If users is a queryset, let ORM do the filtering
        return users.filter(profile__roles__name=role_name)
    except Exception:
        try:
            return [u for u in users if getattr(u, 'profile', None) and u.profile.has_role(role_name)]
        except Exception:
            return []
