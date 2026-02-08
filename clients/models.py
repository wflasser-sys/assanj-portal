"""
Client model representing clients registered by fetchers.
Each client belongs to a fetcher who registered them.
"""

from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    """
    Client model - represents business clients registered by fetchers.
    Fetchers can only see clients they created.
    """
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='clients',
        help_text="Fetcher who registered this client"
    )
    full_name = models.CharField(max_length=200)
    business_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    city = models.CharField(max_length=100)
    business_category = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='client')
    date_created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_created']
    
    def __str__(self):
        return f"{self.business_name} - {self.full_name}"


# Ensure that if a Client is linked to a Django User, that user's profile has the 'client' role
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Client)
def assign_client_role(sender, instance, created, **kwargs):
    """If a Client has an associated User, ensure their UserProfile contains 'client' role."""
    try:
        if instance.user:
            from accounts.models import UserProfile
            profile, _ = UserProfile.objects.get_or_create(user=instance.user)
            # Add role using helper (creates Role if missing)
            profile.add_role('client')
            profile.save()
    except Exception:
        # Be conservative: fail silently to avoid breaking client creation flows
        pass
