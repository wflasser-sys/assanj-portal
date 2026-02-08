from django import forms
from .models import Lead


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        # Allow callers to choose status and provide meeting details on add/edit
        fields = ['business_name', 'phone_number', 'category', 'other_category', 'status', 'meeting_details']
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': 'Business name'}),
            'phone_number': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': 'Phone number'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'other_category': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500', 'placeholder': 'If other, specify...'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500'}),
            'meeting_details': forms.Textarea(attrs={'class': 'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500', 'rows':3, 'placeholder':'Meeting details (time, notes)'}),
        }


class AdminLeadForm(LeadForm):
    """Form used by admins to edit leads and assign a sales closer."""
    assigned_sales_closer = forms.ModelChoiceField(queryset=__import__('django.contrib.auth.models', fromlist=['User']).User.objects.all(), required=False,
                                                   widget=forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded-md'}))

    class Meta(LeadForm.Meta):
        fields = LeadForm.Meta.fields + ['assigned_sales_closer']
