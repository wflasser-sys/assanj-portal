"""
Admin configuration for Project model.
"""

from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client', 'project_type', 'status', 
        'assigned_to', 'payment_status', 'date_created'
    )
    list_filter = ('status', 'project_type', 'website_type', 'payment_status')
    search_fields = ('client__business_name', 'client__full_name')
    readonly_fields = ('date_created', 'date_assigned', 'date_completed')
    
    fieldsets = (
        ('Client & Fetcher', {
            'fields': ('client', 'created_by')
        }),
        ('Project Details', {
            'fields': (
                'project_type', 'website_type', 'pages_required',
                'business_description', 'services_list'
            )
        }),
        ('Contact Information', {
            'fields': (
                'contact_info_phone', 'contact_info_email', 
                'contact_info_address', 'google_map_link'
            )
        }),
        ('Social Media', {
            'fields': ('social_instagram', 'social_facebook', 'social_whatsapp')
        }),
        ('Assets', {
            'fields': ('logo_drive_link', 'photos_drive_link')
        }),
        ('Design', {
            'fields': ('design_style', 'reference_websites')
        }),
        ('Domain & Hosting', {
            'fields': (
                'has_domain', 'has_hosting',
                'needs_domain_assistance', 'needs_hosting_assistance',
                'needs_maintenance_plan'
            )
        }),
        ('Payment', {
            'fields': (
                'payment_status', 'payment_proof',
                'referral_used', 'referrer_name'
            )
        }),
        ('Assignment & Status', {
            'fields': (
                'assigned_to', 'status', 'deadline',
                'date_created', 'date_assigned', 'date_completed'
            )
        }),
        ('Developer Work', {
            'fields': (
                'developer_mock_link', 'final_delivery_link', 
                'developer_notes'
            )
        }),
        ('Payouts', {
            'fields': (
                'admin_payment_released',
                'fetcher_commission_amount', 'developer_payout_amount',
                'agency_profit'
            )
        }),
    )
