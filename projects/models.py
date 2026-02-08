import json
from django.db import models
from django.contrib.auth.models import User
from clients.models import Client


class Project(models.Model):
    """
    Main project model with complete workflow tracking.
    Workflow: New -> Assigned -> In-Progress -> Completed -> Payment Done
    """
    
    PROJECT_TYPE_CHOICES = [
        ('professional_10k', 'Professional 10k'),
        ('professional_15k', 'Professional 15k'),
        ('professional_25k', 'Professional 25k'),
        ('professional_40k', 'Professional 40k'),
        ('custom', 'Custom'),
    ]
    
    WEBSITE_TYPE_CHOICES = [
        ('landing', 'Landing Page'),
        ('business', 'Business Website'),
        ('portfolio', 'Portfolio'),
        ('service', 'Service Website'),
        ('ecom-lite', 'E-commerce Lite'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('payment_done', 'Payment Done'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('paid_advance', 'Paid Advance'),
        ('paid_full', 'Paid Full'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='projects')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_projects',
        help_text="Fetcher who submitted this project"
    )
    
    project_type = models.CharField(max_length=50, choices=PROJECT_TYPE_CHOICES)
    website_type = models.CharField(max_length=50, choices=WEBSITE_TYPE_CHOICES)
    pages_required = models.TextField(
        help_text="JSON list of required pages",
        default='[]'
    )
    business_description = models.TextField()
    services_list = models.TextField(
        help_text="JSON list of services",
        default='[]'
    )
    
    contact_info_phone = models.CharField(max_length=20)
    contact_info_email = models.EmailField()
    contact_info_address = models.TextField()
    
    google_map_link = models.URLField(blank=True, null=True)
    social_instagram = models.URLField(blank=True, null=True)
    social_facebook = models.URLField(blank=True, null=True)
    social_whatsapp = models.CharField(max_length=20, blank=True, null=True)
    
    logo_drive_link = models.URLField(blank=True, null=True)
    photos_drive_link = models.URLField(blank=True, null=True)
    
    design_style = models.CharField(max_length=200, blank=True, null=True)
    reference_websites = models.TextField(
        help_text="JSON list of reference websites",
        default='[]'
    )
    
    has_domain = models.BooleanField(default=False)
    has_hosting = models.BooleanField(default=False)
    needs_domain_assistance = models.BooleanField(default=False)
    needs_hosting_assistance = models.BooleanField(default=False)
    needs_maintenance_plan = models.BooleanField(default=False)
    
    deadline = models.DateField()
    
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='not_paid'
    )
    payment_proof = models.ImageField(
        upload_to='payment_proofs/', 
        blank=True, 
        null=True
    )
    
    referral_used = models.BooleanField(default=False)
    referrer_name = models.CharField(max_length=200, blank=True, null=True)
    
    # Link to Lead (optional)
    lead = models.ForeignKey('leads.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')

    # Financial fields
    total_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    monthly_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    payment_40_received = models.BooleanField(default=False)
    payment_60_received = models.BooleanField(default=False)

    # Assigned team members (designers, developers, seo, gbp, etc.)
    assigned_team = models.ManyToManyField(User, related_name='team_projects', blank=True)

    # Project workflow stage (strict order enforced in views)
    STAGE_CHOICES = [
        ('assigned', 'Assigned'),
        ('design', 'Design'),
        ('landing_dev', 'Landing Page Development'),
        ('client_approval_landing', 'Client Approval (Landing)'),
        ('full_dev', 'Full Website Development'),
        ('client_approval_final', 'Client Approval (Final)'),
        ('deployment', 'Deployment'),
        ('seo_gbp_ongoing', 'SEO + GBP Ongoing'),
        ('completed', 'Completed'),
    ]
    current_stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='design')

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_projects',
        help_text="Developer assigned to this project"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new'
    )

    date_created = models.DateTimeField(auto_now_add=True)
    date_assigned = models.DateTimeField(null=True, blank=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    
    developer_mock_link = models.URLField(blank=True, null=True)
    final_delivery_link = models.URLField(blank=True, null=True)
    developer_notes = models.TextField(blank=True, null=True)
    
    admin_payment_released = models.BooleanField(default=False)
    fetcher_commission_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    developer_payout_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    agency_profit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )

    # Per-role explicit payouts (optional)
    designer_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    seo_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    gbp_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    social_media_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Optional per-user payouts stored as JSON: {"user_id": amount}
    assigned_payments = models.JSONField(default=dict, blank=True, null=True)

    def get_user_payout(self, user):
        """Return payout amount for a specific user for this project."""
        if not user:
            return 0
        # If user is the main assigned developer use developer_payout_amount
        if self.assigned_to and self.assigned_to == user and self.developer_payout_amount:
            return float(self.developer_payout_amount)
        # Check assigned_payments mapping
        try:
            payments = self.assigned_payments or {}
            uid = str(user.id)
            # support both str keys and int keys
            if uid in payments:
                return float(payments[uid])
            if user.id in payments:
                return float(payments[user.id])
        except Exception:
            return 0
        return 0


class ProjectUpdate(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='updates')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    links = models.TextField(blank=True, null=True, help_text='Optional links or notes (one per line)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Update for Project #{self.project.id} by {self.user} at {self.created_at}"

    def links_list(self):
        return [l.strip() for l in (self.links or '').splitlines() if l.strip()]
