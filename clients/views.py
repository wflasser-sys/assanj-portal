"""
Views for Client management.
Fetchers can create clients and view their own clients.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView
from django.urls import reverse
from django.contrib import messages
from accounts.mixins import FetcherRequiredMixin, SalesCloserRequiredMixin
from .models import Client
from .forms import ClientForm

class CreateClientView(SalesCloserRequiredMixin, CreateView):
    # Allow sales closers, admins and project managers to access this view
    allowed_roles = ['sales_closer', 'admin', 'project_manager']
    model = Client
    form_class = ClientForm
    template_name = 'add_client.html'

    # RoleRequiredMixin will enforce `allowed_roles` so a separate dispatch
    # override is not necessary here.

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        profile = getattr(self.request.user, 'profile', None)
        can_set_payouts = False
        if profile and (profile.has_role('admin') or profile.has_role('project_manager')):
            can_set_payouts = True
        kwargs['can_set_payouts'] = can_set_payouts
        return kwargs

    def form_valid(self, form):
        # Store cleaned client data in session instead of saving
        # Convert Decimal values (and other non-JSON types) to strings so the session (JSON serializer) can persist them
        client_data = {}
        for k, v in form.cleaned_data.items():
            try:
                client_data[k] = str(v) if not isinstance(v, (str, int, bool)) else v
            except Exception:
                client_data[k] = str(v)

        # If the creator is not allowed to set payouts, remove payout keys before storing
        profile = getattr(self.request.user, 'profile', None)
        if not (profile and (profile.has_role('admin') or profile.has_role('project_manager'))):
            for key in ['fetcher_commission_amount', 'developer_payout_amount', 'agency_profit', 'designer_payout_amount', 'seo_payout_amount', 'gbp_payout_amount', 'social_media_payout_amount']:
                client_data.pop(key, None)

        self.request.session['new_client_data'] = client_data
        self.request.session.modified = True

        return redirect('projects:fetcher_add_project')



class FetcherClientListView(FetcherRequiredMixin, ListView):
    """View for fetchers to see their clients."""
    model = Client
    template_name = 'client_list.html'
    context_object_name = 'clients'
    
    paginate_by = 10

    def get_queryset(self):
        return Client.objects.filter(created_by=self.request.user)
