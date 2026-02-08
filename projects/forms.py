"""
Forms for Project creation and management.
"""

import json
from django import forms
from django.contrib.auth.models import User
from .models import Project


class ProjectForm(forms.ModelForm):
    """
    Form for creating a new project (used by fetchers).
    Handles all project submission fields.
    """
    
    pages_required_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter required pages (one per line)\nExample:\nHome\nAbout Us\nServices\nContact',
            'rows': 5
        }),
        required=False,
        label='Pages Required'
    )
    
    services_list_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter services (one per line)\nExample:\nWeb Design\nSEO\nMaintenance',
            'rows': 5
        }),
        required=False,
        label='Services List'
    )
    
    reference_websites_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter reference website URLs (one per line)',
            'rows': 3
        }),
        required=False,
        label='Reference Websites'
    )
    
    class Meta:
        model = Project
        fields = [
            'project_type',
            'website_type',
            'business_description',
            'contact_info_phone',
            'contact_info_email',
            'contact_info_address',
            'google_map_link',
            'social_instagram',
            'social_facebook',
            'social_whatsapp',
            'logo_drive_link',
            'photos_drive_link',
            'design_style',
            'has_domain',
            'has_hosting',
            'needs_domain_assistance',
            'needs_hosting_assistance',
            'needs_maintenance_plan',
            'deadline',
            'payment_status',
            'payment_proof',
            'referral_used',
            'referrer_name',
        ]
        widgets = {
            'business_description': forms.Textarea(attrs={
                'placeholder': 'Describe the business...',
                'rows': 4
            }),
            'contact_info_address': forms.Textarea(attrs={
                'placeholder': 'Full address',
                'rows': 2
            }),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'design_style': forms.TextInput(attrs={
                'placeholder': 'e.g., Modern, Minimalist, Corporate'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['pages_required_text'].initial = '\n'.join(
                self.instance.get_pages_list()
            )
            self.fields['services_list_text'].initial = '\n'.join(
                self.instance.get_services_list()
            )
            self.fields['reference_websites_text'].initial = '\n'.join(
                self.instance.get_reference_websites_list()
            )
    
    def clean_pages_required_text(self):
        text = self.cleaned_data.get('pages_required_text', '')
        pages = [p.strip() for p in text.split('\n') if p.strip()]
        return json.dumps(pages)
    
    def clean_services_list_text(self):
        text = self.cleaned_data.get('services_list_text', '')
        services = [s.strip() for s in text.split('\n') if s.strip()]
        return json.dumps(services)
    
    def clean_reference_websites_text(self):
        text = self.cleaned_data.get('reference_websites_text', '')
        websites = [w.strip() for w in text.split('\n') if w.strip()]
        return json.dumps(websites)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.pages_required = self.cleaned_data.get('pages_required_text', '[]')
        instance.services_list = self.cleaned_data.get('services_list_text', '[]')
        instance.reference_websites = self.cleaned_data.get('reference_websites_text', '[]')
        if commit:
            instance.save()
        return instance


class AdminAssignForm(forms.Form):
    """Form for admin to assign developer and set payouts."""
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Assign to Developer',
        required=True
    )
    fetcher_commission_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Fetcher Commission'
    )
    developer_payout_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Developer Payout'
    )
    agency_profit = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Agency Profit'
    )
    # Additional payouts
    designer_payout_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Designer Payout'
    )
    seo_payout_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='SEO Payout'
    )
    gbp_payout_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='GBP Payout'
    )
    social_media_payout_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Social Media Payout'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(
            profile__roles__name='developer'
        )
        # Add assigned team selection (designers, developers, seo, gbp)
        self.fields['assigned_team'] = forms.ModelMultipleChoiceField(
            queryset=User.objects.filter(profile__roles__name__in=['designer', 'developer', 'seo', 'gbp']).distinct(),
            required=False,
            label='Assigned Team'
        )
        # Manual per-user payouts (one per line as username:amount or user_id:amount)
        self.fields['assigned_payments'] = forms.CharField(
            widget=forms.Textarea(attrs={'rows':4, 'placeholder': 'username:amount per line\ne.g. alice:2500\n22:1000'}),
            required=False,
            label='Assigned Payments (per user)'
        )


class DeveloperUpdateForm(forms.ModelForm):
    """Form for developers to update project status and add links."""
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=True)
    
    class Meta:
        model = Project
        fields = [
            'developer_mock_link',
            'final_delivery_link',
            'developer_notes',
            'status',
        ]
        widgets = {
            'developer_notes': forms.Textarea(attrs={
                'placeholder': 'Add notes about the project...',
                'rows': 4
            }),
            'developer_mock_link': forms.URLInput(attrs={
                'placeholder': 'https://mock-design-link.com'
            }),
            'final_delivery_link': forms.URLInput(attrs={
                'placeholder': 'https://final-website-link.com'
            }),
        }
