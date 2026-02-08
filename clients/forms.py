"""
Forms for Client creation.
"""

from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    """Form for creating a new client (used by fetchers)."""
    class Meta:
        model = Client
        fields = [
            'full_name',
            'business_name',
            'phone',
            'email',
            'city',
            'business_category',
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Client Full Name'}),
            'business_name': forms.TextInput(attrs={'placeholder': 'Business Name'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'business_category': forms.TextInput(attrs={'placeholder': 'Business Category'}),
        }

    # Default payout fields for projects created for this client
    fetcher_commission_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Default Fetcher Commission')
    developer_payout_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Default Developer Payout')
    agency_profit = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Default Agency Profit')
    designer_payout_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Default Designer Payout')
    seo_payout_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Default SEO Payout')
    gbp_payout_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Default GBP Payout')
    social_media_payout_amount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Default Social Media Payout')

    def __init__(self, *args, **kwargs):
        # `can_set_payouts` controls whether the form should expose default payout fields
        can_set_payouts = kwargs.pop('can_set_payouts', False)
        super().__init__(*args, **kwargs)
        if not can_set_payouts:
            # Remove payout fields from the form if the user is not allowed to set them
            for f in ['fetcher_commission_amount', 'developer_payout_amount', 'agency_profit', 'designer_payout_amount', 'seo_payout_amount', 'gbp_payout_amount', 'social_media_payout_amount']:
                if f in self.fields:
                    self.fields.pop(f)
