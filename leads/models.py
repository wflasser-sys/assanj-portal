from django.db import models
from django.contrib.auth.models import User


class Lead(models.Model):
    CATEGORY_CHOICES = [
        ('Dentist', 'Dentist'),
        ('Construction', 'Construction'),
        ('Clinic', 'Clinic'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('meeting_booked', 'Meeting Booked'),
        ('deal_won', 'Deal Won'),
        ('deal_lost', 'Deal Lost'),
    ]

    business_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    other_category = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='new')
    assigned_sales_closer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_leads'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_leads'
    )
    meeting_details = models.TextField(blank=True, null=True, help_text='Optional details/time for meetings')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} ({self.phone_number})"
