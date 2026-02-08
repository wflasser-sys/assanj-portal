from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Lead
from .forms import LeadForm, AdminLeadForm
from accounts.mixins import SalesCloserRequiredMixin
from django.views import View
from projects.models import Project
from activity.utils import log_activity
from django.db import models

@login_required
def cold_caller_dashboard(request):
    if not (
        request.user.profile.has_role('cold_caller')
        or request.user.profile.has_role('project_manager')
        or request.user.profile.has_role('admin')
    ):
        messages.error(request, 'Access denied. You do not have permissions to view leads.')
        return redirect('cold_caller_dashboard')

    show_my_leads = request.GET.get('my_leads') == '1'

    if show_my_leads:
        leads = Lead.objects.filter(created_by=request.user).order_by('-created_at')
    else:
        leads = Lead.objects.all().order_by('-created_at')

    my_leads = Lead.objects.filter(created_by=request.user)

    projects = Project.objects.filter(lead__in=my_leads)
    total_earned = projects.aggregate(
        models.Sum('fetcher_commission_amount')
    )['fetcher_commission_amount__sum'] or 0

    pending = projects.filter(
        payment_status__in=['not_paid', 'paid_advance']
    ).aggregate(
        models.Sum('fetcher_commission_amount')
    )['fetcher_commission_amount__sum'] or 0

    context = {
        'total_earned': total_earned,
        'pending': pending,
        'form': LeadForm(),
        'leads': leads,
        'show_my_leads': show_my_leads,
    }
    return render(request, 'cold_caller_dashboard.html', context)


@login_required
def add_lead(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.created_by = request.user
            lead.save()
            # Log meeting details when meeting_booked
            if lead.status == 'meeting_booked' and lead.meeting_details:
                log_activity('meeting_booked', 'lead', lead.id, request.user, note=lead.meeting_details)
            log_activity('create_lead', 'lead', lead.id, request.user)
            messages.success(request, 'Lead created successfully.')
            return redirect('leads:cold_caller_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    return redirect('leads:cold_caller_dashboard')


@login_required
def edit_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    # cold caller can edit only own leads; admin can edit all
    if not (request.user.profile.has_role('admin') or request.user.profile.has_role('project_manager')  or lead.created_by == request.user):
        messages.error(request, 'You do not have permission to edit this lead.')
        return redirect('leads:cold_caller_dashboard')

    if request.method == 'POST':
        # Admins can assign a sales closer, others cannot
        if request.user.profile.has_role('admin'):
            form = AdminLeadForm(request.POST, instance=lead)
        else:
            # Ensure the assigned_sales_closer cannot be changed by non-admins
            post = request.POST.copy()
            post.pop('assigned_sales_closer', None)
            form = LeadForm(post, instance=lead)

        if form.is_valid():
            form.save()
            log_activity('edit_lead', 'lead', lead.id, request.user)
            messages.success(request, 'Lead updated successfully.')
            return redirect('leads:cold_caller_dashboard')
    else:
        if request.user.profile.has_role('admin'):
            form = AdminLeadForm(instance=lead)
        else:
            form = LeadForm(instance=lead)

    return render(request, 'edit_lead.html', {'form': form, 'lead': lead})


@login_required
def delete_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if not (request.user.profile.has_role('admin') or request.user.profile.has_role('project_manager') or lead.created_by == request.user):
        messages.error(request, 'You do not have permission to delete this lead.')
        return redirect('leads:cold_caller_dashboard')

    lead.delete()
    log_activity('delete_lead', 'lead', pk, request.user)
    messages.success(request, 'Lead deleted successfully.')
    return redirect('leads:cold_caller_dashboard')


class SalesCloserDashboardView(View):
    def get(self, request):
        if not request.user.profile.has_role('sales_closer') and not request.user.profile.has_role('admin') and not request.user.profile.has_role('project_manager'):
            messages.error(request, 'You do not have permission to view this page.')
            return redirect('dashboard:dashboard')
        leads = Lead.objects.filter(assigned_sales_closer=request.user)
        # summary
        deals_won = leads.filter(status='deal_won').count()
        meetings = leads.filter(status='meeting_booked').count()
        # sum value of projects created from these leads (if any)
        from projects.models import Project
        projects = Project.objects.filter(lead__in=leads)
        total_value = projects.aggregate(models.Sum('total_price'))['total_price__sum'] or 0
        return render(request, 'sales_closer_dashboard.html', {'leads': leads, 'deals_won': deals_won, 'meetings': meetings, 'total_value': total_value})

@login_required
def filter_leads(request):
    """Filter leads by status and search term for the current user (callers see their leads)."""
    if not (request.user.profile.has_role('cold_caller') or request.user.profile.has_role('sales_closer') or request.user.profile.has_role('admin') or request.user.profile.has_role('project_manager')):
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')

    status = request.GET.get('status')
    q = request.GET.get('q', '').strip()

    qs = Lead.objects.all()
    # If caller, restrict to their leads
    if request.user.profile.has_role('cold_caller') and not request.user.profile.has_role('admin'):
        qs = qs.filter(created_by=request.user)
    # If sales_closer, restrict to assigned leads
    if request.user.profile.has_role('sales_closer') and not request.user.profile.has_role('admin'):
        qs = qs.filter(assigned_sales_closer=request.user)

    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(business_name__icontains=q)

    return render(request, 'filter.html', {'leads': qs})


@login_required
def sales_closer_onboard(request):
    """Create client + starter project from Sales Closer dashboard (onboarding flow)."""
    if not (request.user.profile.has_role('sales_closer') or request.user.profile.has_role('admin') or request.user.profile.has_role('project_manager')):
        messages.error(request, 'You do not have permission to onboard clients.')
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        business_name = request.POST.get('business_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        city = request.POST.get('city', '').strip()

        if not business_name or not phone:
            messages.error(request, 'Please provide at least business name and phone.')
            return redirect('leads:sales_closer_dashboard')

        # Store the client info in session and redirect to the full project creation form.
        client_data = {
            'business_name': business_name,
            'phone': phone,
            'email': email,
            'city': city,
        }
        # Sales closers shouldn't be able to set payout defaults here
        request.session['new_client_data'] = client_data
        request.session.modified = True

        # Log that onboarding was started (entity_id 0 as placeholder)
        log_activity('sales_closer_onboard_started', 'client', 0, request.user)

        messages.success(request, 'Client info saved. Please complete the full project details to finish onboarding.')
        return redirect('projects:fetcher_add_project')

    # If GET, render a dedicated onboarding form (no payouts assigned here)
    return render(request, 'onboard_client.html')


@login_required
def mark_won(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    # only assigned sales closer or admin
    if not (request.user.profile.has_role('admin')  or request.user.profile.has_role('project_manager') or lead.assigned_sales_closer == request.user):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('leads:sales_closer_dashboard')

    lead.status = 'deal_won'
    lead.save()

    # Create a Project automatically and assign to admin/project_manager
    client = None
    # If a Client matching business_name exists, link, else create a Client
    from clients.models import Client
    client_obj, created = Client.objects.get_or_create(business_name=lead.business_name, defaults={'phone': lead.phone_number, 'created_by': lead.created_by})

    # Create project with created_by as the cold caller who created the lead (so they see it in their projects list)
    creator = lead.created_by if lead.created_by else User.objects.filter(profile__roles__name='admin').first()
    
    project = Project.objects.create(
        client=client_obj,
        created_by=creator,
        project_type='custom',
        website_type='business',
        pages_required='[]',
        services_list='[]',
        business_description='',
        contact_info_phone=lead.phone_number,
        contact_info_email='',
        contact_info_address='',
        deadline='2099-12-31',
        status='assigned'
    )
    project.lead = lead
    project.save()

    # Move ownership to admin/project manager (we leave created_by as a system admin if not assigned)
    log_activity('lead_marked_won', 'lead', lead.id, request.user)
    log_activity('project_created', 'project', project.id, request.user)

    messages.success(request, 'Lead marked as won and project created successfully.')
    return redirect('leads:sales_closer_dashboard')


@login_required
def mark_lost(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if not (request.user.profile.has_role('admin')  or request.user.profile.has_role('project_manager') or lead.assigned_sales_closer == request.user):
        messages.error(request, 'You do not have permission to perform this action.')
        return redirect('leads:sales_closer_dashboard')

    lead.status = 'deal_lost'
    lead.save()
    log_activity('lead_marked_lost', 'lead', lead.id, request.user)
    messages.success(request, 'Lead marked as lost.')
    return redirect('leads:sales_closer_dashboard')

    messages.success(request, 'Lead marked as lost.')
    return redirect('leads:sales_closer_dashboard')
