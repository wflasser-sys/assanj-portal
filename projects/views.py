"""
Views for Project management.
Handles the complete project workflow for all roles.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, ListView, DetailView, UpdateView
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from accounts.mixins import FetcherRequiredMixin, AdminRequiredMixin, DeveloperRequiredMixin, ProjectExecutionMixin, ProjectManagerRequiredMixin
from clients.models import Client
from .models import Project, ProjectUpdate
from .forms import ProjectForm, AdminAssignForm, DeveloperUpdateForm

from django.db import transaction, models
from activity.utils import log_activity
from .cache_utils import invalidate_admin_cache, invalidate_user_fetcher_cache
class CreateProjectView(FetcherRequiredMixin, CreateView):
    # Allow cold callers, sales closers, project managers and admins to create projects
    allowed_roles = ['cold_caller', 'sales_closer', 'project_manager', 'admin']
    model = Project
    form_class = ProjectForm
    template_name = 'add_project.html'

    # RoleRequiredMixin will enforce `allowed_roles` so the manual dispatch
    # check is not needed here.

    def form_valid(self, form):
        client_data = self.request.session.get('new_client_data')

        if not client_data:
            messages.error(self.request, "Missing client data. Please start again.")
            return redirect('fetcher_add_client')

        # If the user is a sales_closer (and not admin), require full project details
        profile = getattr(self.request.user, 'profile', None)
        if profile and profile.has_role('sales_closer') and not profile.has_role('admin'):
            missing = []
            for field_name in ['project_type', 'website_type', 'business_description', 'deadline']:
                if not form.cleaned_data.get(field_name):
                    missing.append(field_name)
            # Contact: at least phone or email
            if not form.cleaned_data.get('contact_info_phone') and not form.cleaned_data.get('contact_info_email'):
                missing.append('contact_info_phone')
            # pages and services must be provided (ProjectForm returns JSON '[]' for empty)
            if form.cleaned_data.get('pages_required_text', '[]') == '[]':
                missing.append('pages_required_text')
            if form.cleaned_data.get('services_list_text', '[]') == '[]':
                missing.append('services_list_text')
            if missing:
                for f in missing:
                    # Add error to the form so template shows it
                    form.add_error(f if f in form.fields else None, 'This field is required to complete project onboarding.')
                return self.form_invalid(form)

        with transaction.atomic():

            # 1. Create the client now
            # Ensure we only pass valid Client model fields (remove payout defaults from client payload)
            client_create_data = client_data.copy()
            for key in ['fetcher_commission_amount', 'developer_payout_amount', 'agency_profit', 'designer_payout_amount', 'seo_payout_amount', 'gbp_payout_amount', 'social_media_payout_amount']:
                client_create_data.pop(key, None)

            client = Client.objects.create(
                created_by=self.request.user,
                **client_create_data
            )

            # 2. Create the project
            project = form.save(commit=False)
            project.client = client
            project.created_by = self.request.user
            project.status = "new"
            # Apply client-default payouts if present
            client_defaults = self.request.session.get('new_client_data', {})
            from decimal import Decimal, InvalidOperation

            def _coerce_decimal(v):
                if v is None:
                    return None
                if isinstance(v, (int, float, Decimal)):
                    return Decimal(str(v))
                s = str(v).strip()
                if s == '' or s.lower() == 'none':
                    return None
                try:
                    return Decimal(s)
                except (InvalidOperation, ValueError):
                    return None

            try:
                val = _coerce_decimal(client_defaults.get('fetcher_commission_amount'))
                if val is not None:
                    project.fetcher_commission_amount = val
                val = _coerce_decimal(client_defaults.get('developer_payout_amount'))
                if val is not None:
                    project.developer_payout_amount = val
                val = _coerce_decimal(client_defaults.get('agency_profit'))
                if val is not None:
                    project.agency_profit = val
                val = _coerce_decimal(client_defaults.get('designer_payout_amount'))
                if val is not None:
                    project.designer_payout_amount = val
                val = _coerce_decimal(client_defaults.get('seo_payout_amount'))
                if val is not None:
                    project.seo_payout_amount = val
                val = _coerce_decimal(client_defaults.get('gbp_payout_amount'))
                if val is not None:
                    project.gbp_payout_amount = val
                val = _coerce_decimal(client_defaults.get('social_media_payout_amount'))
                if val is not None:
                    project.social_media_payout_amount = val
            except Exception:
                pass

            project.save()
            log_activity('project_created', 'project', project.id, self.request.user)

        # Clear session
        del self.request.session['new_client_data']
        
        # Invalidate relevant caches
        invalidate_admin_cache()
        invalidate_user_fetcher_cache(self.request.user.id)

        messages.success(
            self.request,
            f"Project created successfully for {client.business_name}!"
        )
        return redirect('projects:fetcher_projects')


class FetcherProjectListView(FetcherRequiredMixin, ListView):
    """View for fetchers to see their submitted projects."""
    model = Project
    template_name = 'project_list_fetcher.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = self.get_queryset()
        # earnings for fetcher: sum fetcher_commission_amount for projects where admin_payment_released
        total = 0
        pending = 0
        for p in projects:
            if p.admin_payment_released and p.fetcher_commission_amount:
                total += float(p.fetcher_commission_amount)
            elif p.status == 'completed' and not p.admin_payment_released and p.fetcher_commission_amount:
                pending += float(p.fetcher_commission_amount)
        context['total_earnings'] = total
        context['pending_earnings'] = pending
        return context


class FetcherProjectDetailView(FetcherRequiredMixin, DetailView):
    """View for fetchers to see project details (read-only)."""
    model = Project
    template_name = 'project_detail_fetcher.html'
    context_object_name = 'project'

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)



# ============ ADMIN DASHBOARD VIEW ============
class AdminProjectListView(ProjectManagerRequiredMixin, ListView):
    """View for admin/project manager to see all projects."""
    model = Project
    template_name = 'dashboard_admin.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.all().select_related('client', 'created_by',
                                                    'assigned_to')

    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        
        context = super().get_context_data(**kwargs)
        projects = self.get_queryset()

        # Cache project status counts - 5 minute cache
        cache_key = 'admin_projects_status_counts'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            context['new_projects'] = cached_data['new_projects']
            context['assigned_projects'] = cached_data['assigned_projects']
            context['in_progress_projects'] = cached_data['in_progress_projects']
            context['completed_projects'] = cached_data['completed_projects']
            context['payment_done_projects'] = cached_data['payment_done_projects']
        else:
            context['new_projects'] = projects.filter(status='new')
            context['assigned_projects'] = projects.filter(status='assigned')
            context['in_progress_projects'] = projects.filter(status='in_progress')
            context['completed_projects'] = projects.filter(status='completed')
            context['payment_done_projects'] = projects.filter(status='payment_done')
            
            cache.set(cache_key, {
                'new_projects': context['new_projects'],
                'assigned_projects': context['assigned_projects'],
                'in_progress_projects': context['in_progress_projects'],
                'completed_projects': context['completed_projects'],
                'payment_done_projects': context['payment_done_projects'],
            }, 300)  # 5 minutes

        # Cache leads overview - 5 minute cache
        cache_key_leads = 'admin_leads_overview'
        cached_leads = cache.get(cache_key_leads)
        
        if cached_leads:
            context['leads_new'] = cached_leads['leads_new']
            context['leads_contacted'] = cached_leads['leads_contacted']
            context['leads_meetings'] = cached_leads['leads_meetings']
            context['leads_won'] = cached_leads['leads_won']
            context['leads_lost'] = cached_leads['leads_lost']
        else:
            from leads.models import Lead
            context['leads_new'] = Lead.objects.filter(status='new')
            context['leads_contacted'] = Lead.objects.filter(status='contacted')
            context['leads_meetings'] = Lead.objects.filter(status='meeting_booked')
            context['leads_won'] = Lead.objects.filter(status='deal_won')
            context['leads_lost'] = Lead.objects.filter(status='deal_lost')
            
            cache.set(cache_key_leads, {
                'leads_new': context['leads_new'],
                'leads_contacted': context['leads_contacted'],
                'leads_meetings': context['leads_meetings'],
                'leads_won': context['leads_won'],
                'leads_lost': context['leads_lost'],
            }, 300)  # 5 minutes
        
        # Cache agency earnings calculations - 10 minute cache
        cache_key_earnings = 'admin_agency_earnings'
        cached_earnings = cache.get(cache_key_earnings)
        
        if cached_earnings:
            context['total_profit'] = cached_earnings['total_profit']
            context['pending_profit'] = cached_earnings['pending_profit']
        else:
            total_profit = projects.filter(
                admin_payment_released=True
            ).aggregate(
                total=Sum('agency_profit')
            )['total'] or 0
            
            pending_profit = projects.filter(
                status='completed',
                admin_payment_released=False
            ).aggregate(
                total=Sum('agency_profit')
            )['total'] or 0
            
            context['total_profit'] = total_profit
            context['pending_profit'] = pending_profit
            
            cache.set(cache_key_earnings, {
                'total_profit': total_profit,
                'pending_profit': pending_profit,
            }, 600)  # 10 minutes

        return context

class AdminProjectDetailView(ProjectManagerRequiredMixin, DetailView):
    """View for admin/project manager to see full project details."""
    model = Project
    template_name = 'project_detail_admin.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Cache developers list - 30 minute cache
        cache_key = 'admin_developers_list'
        cached_developers = cache.get(cache_key)
        
        if cached_developers:
            context['developers'] = cached_developers
        else:
            developers = User.objects.filter(profile__roles__name='developer')
            context['developers'] = developers
            cache.set(cache_key, developers, 1800)  # 30 minutes
        
        # Prepare assigned_payments textarea initial
        payments_initial = ''
        try:
            for uid, amt in (self.object.assigned_payments or {}).items():
                try:
                    u = User.objects.get(pk=int(uid))
                    payments_initial += f"{u.username}:{amt}\n"
                except Exception:
                    payments_initial += f"{uid}:{amt}\n"
        except Exception:
            payments_initial = ''

        context['assign_form'] = AdminAssignForm(
            initial={
                'assigned_to': self.object.assigned_to,
                'assigned_team': self.object.assigned_team.all(),
                'fetcher_commission_amount': self.object.fetcher_commission_amount,
                'developer_payout_amount': self.object.developer_payout_amount,
                'agency_profit': self.object.agency_profit,
                'assigned_payments': payments_initial,
            })
        return context

from django.views import View

class AdminAssignDeveloperView(ProjectManagerRequiredMixin, View):
    template_name = 'admin_assign.html'

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])

        # Convert assigned_payments dict into "username:amount" lines for initial textarea
        payments_initial = ''
        try:
            for uid, amt in (project.assigned_payments or {}).items():
                try:
                    u = User.objects.get(pk=int(uid))
                    payments_initial += f"{u.username}:{amt}\n"
                except Exception:
                    payments_initial += f"{uid}:{amt}\n"
        except Exception:
            payments_initial = ''

        assign_form = AdminAssignForm(initial={
            'assigned_to': project.assigned_to,
            'fetcher_commission_amount': project.fetcher_commission_amount,
            'developer_payout_amount': project.developer_payout_amount,
            'agency_profit': project.agency_profit,
            'designer_payout_amount': project.designer_payout_amount,
            'seo_payout_amount': project.seo_payout_amount,
            'gbp_payout_amount': project.gbp_payout_amount,
            'social_media_payout_amount': project.social_media_payout_amount,
            'assigned_payments': payments_initial,
        })

        return render(request, self.template_name, {
            'project': project,
            'assign_form': assign_form
        })

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        form = AdminAssignForm(request.POST)

        if form.is_valid():
            developer = form.cleaned_data['assigned_to']

            project.assigned_to = developer
            project.status = 'assigned'
            project.date_assigned = timezone.now()
            # Set initial stage to 'design' as per requirements
            if project.current_stage == 'assigned':
                project.current_stage = 'design'

            if form.cleaned_data.get('fetcher_commission_amount'):
                project.fetcher_commission_amount = form.cleaned_data['fetcher_commission_amount']
            if form.cleaned_data.get('developer_payout_amount'):
                project.developer_payout_amount = form.cleaned_data['developer_payout_amount']
            if form.cleaned_data.get('agency_profit'):
                project.agency_profit = form.cleaned_data['agency_profit']
            # Additional payouts
            if form.cleaned_data.get('designer_payout_amount'):
                project.designer_payout_amount = form.cleaned_data['designer_payout_amount']
            if form.cleaned_data.get('seo_payout_amount'):
                project.seo_payout_amount = form.cleaned_data['seo_payout_amount']
            if form.cleaned_data.get('gbp_payout_amount'):
                project.gbp_payout_amount = form.cleaned_data['gbp_payout_amount']
            if form.cleaned_data.get('social_media_payout_amount'):
                project.social_media_payout_amount = form.cleaned_data['social_media_payout_amount']

            project.save()

            # Assigned team handling
            if 'assigned_team' in form.cleaned_data:
                team = form.cleaned_data['assigned_team']
                project.assigned_team.set(team)

            # Parse per-user assigned payments if provided
            assigned_payments_text = form.cleaned_data.get('assigned_payments', '')
            payments_map = {}
            if assigned_payments_text:
                for line in assigned_payments_text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if ':' in line:
                        left, right = line.split(':', 1)
                        left = left.strip()
                        right = right.strip()
                        try:
                            amount = float(right)
                        except ValueError:
                            continue
                        # try to resolve left as username or id
                        user_obj = None
                        if left.isdigit():
                            try:
                                user_obj = User.objects.get(pk=int(left))
                            except User.DoesNotExist:
                                user_obj = None
                        else:
                            try:
                                user_obj = User.objects.get(username=left)
                            except User.DoesNotExist:
                                user_obj = None
                        if user_obj:
                            payments_map[str(user_obj.id)] = amount
                if payments_map:
                    project.assigned_payments = payments_map

            project.save()

            log_activity('assign_developer', 'project', project.id, request.user)
            
            # Invalidate relevant caches
            invalidate_admin_cache()
            if project.created_by:
                invalidate_user_fetcher_cache(project.created_by.id)

            messages.success(request, f'Project assigned to {developer.username}!')
            return redirect('projects:admin_project_detail', pk=project.pk)

        return render(request, self.template_name, {
            'project': project,
            'assign_form': form
        })


class AdminPaymentReleaseView(ProjectManagerRequiredMixin, DetailView):
    """View for admin/project manager to release payment for a completed project."""
    model = Project
    template_name = 'payment_release.html'
    context_object_name = 'project'

    def post(self, request, *args, **kwargs):
        project = self.get_object()

        if project.status != 'completed':
            messages.error(request,
                           'Cannot release payment for incomplete project.')
            return redirect('projects:admin_project_detail', pk=project.pk)

        project.admin_payment_released = True
        project.status = 'payment_done'
        project.save()
        log_activity('mark_payment_released', 'project', project.id, request.user)
        
        # Invalidate relevant caches
        invalidate_admin_cache()
        if project.created_by:
            invalidate_user_fetcher_cache(project.created_by.id)

        messages.success(request, 'Payment released successfully!')
        return redirect('projects:admin_projects')


class AdminAdvanceStageView(ProjectManagerRequiredMixin, View):
    """Advance project to the next stage in the workflow (admin/project manager only)."""

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        stages = [s[0] for s in Project.STAGE_CHOICES]
        try:
            idx = stages.index(project.current_stage)
        except ValueError:
            messages.error(request, 'Invalid current stage')
            return redirect('projects:admin_project_detail', pk=project.pk)

        if idx + 1 >= len(stages):
            messages.info(request, 'Project is already at the final stage.')
            return redirect('projects:admin_project_detail', pk=project.pk)

        project.current_stage = stages[idx + 1]
        # If reaching completed stage, also flag status
        if project.current_stage == 'completed':
            project.status = 'completed'
        project.save()
        log_activity('advance_stage', 'project', project.id, request.user)
        
        # Invalidate relevant caches
        invalidate_admin_cache()

        messages.success(request, f'Project advanced to {project.get_current_stage_display()}')
        return redirect('projects:admin_project_detail', pk=project.pk)


class AdminUpdateFinancialsView(ProjectManagerRequiredMixin, View):
    """Update financials for a project (prices & payment flags)."""

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])

        total_price = request.POST.get('total_price')
        monthly_price = request.POST.get('monthly_price')
        payment_40 = request.POST.get('payment_40_received') == 'on'
        payment_60 = request.POST.get('payment_60_received') == 'on'

        if total_price:
            try:
                project.total_price = float(total_price)
            except ValueError:
                messages.error(request, 'Invalid total price value')
                return redirect('projects:admin_project_detail', pk=project.pk)
        if monthly_price:
            try:
                project.monthly_price = float(monthly_price)
            except ValueError:
                messages.error(request, 'Invalid monthly price value')
                return redirect('projects:admin_project_detail', pk=project.pk)

        project.payment_40_received = payment_40
        project.payment_60_received = payment_60
        project.save()
        log_activity('update_financials', 'project', project.id, request.user)
        
        # Invalidate relevant caches
        invalidate_admin_cache()

        messages.success(request, 'Project financials updated.')
        return redirect('projects:admin_project_detail', pk=project.pk)


class AdminUpdatePreviewView(ProjectManagerRequiredMixin, View):
    """Upload preview links and notes for client review."""

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        mock_link = request.POST.get('developer_mock_link')
        final_link = request.POST.get('final_delivery_link')
        notes = request.POST.get('developer_notes')

        if mock_link is not None:
            project.developer_mock_link = mock_link
        if final_link is not None:
            project.final_delivery_link = final_link
        if notes is not None:
            project.developer_notes = notes

        project.save()
        log_activity('update_preview_links', 'project', project.id, request.user)
        
        # Invalidate relevant caches
        invalidate_admin_cache()
        
        messages.success(request, 'Preview links updated.')
        return redirect('projects:admin_project_detail', pk=project.pk)


class AdminRevertStageView(ProjectManagerRequiredMixin, View):
    """Revert project to the previous stage (admin/project manager only), with an optional note."""

    def post(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs['pk'])
        stages = [s[0] for s in Project.STAGE_CHOICES]
        try:
            idx = stages.index(project.current_stage)
        except ValueError:
            messages.error(request, 'Invalid current stage')
            return redirect('projects:admin_project_detail', pk=project.pk)

        if idx - 1 < 0:
            messages.info(request, 'Project is already at the earliest stage.')
            return redirect('projects:admin_project_detail', pk=project.pk)

        prev_stage = stages[idx - 1]
        project.current_stage = prev_stage
        # If reverting away from completed, clear completed status
        if project.current_stage != 'completed' and project.status == 'completed':
            project.status = 'in_progress'
        project.save()

        # Create a project update with the admin note (if provided)
        note = request.POST.get('revert_note', '').strip()
        message = f"Stage reverted to {project.get_current_stage_display()} by {request.user.username}."
        if note:
            message += f" Note: {note}"
        ProjectUpdate.objects.create(project=project, user=request.user, message=message)

        # Log activity with note so it appears in project logs
        log_activity('revert_stage', 'project', project.id, request.user, note=message)
        
        # Invalidate relevant caches
        invalidate_admin_cache()

        messages.success(request, f'Project reverted to {project.get_current_stage_display()}')
        return redirect('projects:admin_project_detail', pk=project.pk)

# ============ DEVELOPER DASHBOARD VIEW ============
class DeveloperProjectListView(DeveloperRequiredMixin, ListView):
    """View for developers to see their assigned projects."""
    model = Project
    template_name = 'dashboard_developer.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(assigned_to=self.request.user)

    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        
        context = super().get_context_data(**kwargs)
        projects = self.get_queryset()

        context['assigned_projects'] = projects.filter(status='assigned')
        context['in_progress_projects'] = projects.filter(status='in_progress')
        context['completed_projects'] = projects.filter(
            status__in=['completed', 'payment_done'])
        
        # NEW: Calculate developer earnings
        total_earnings = projects.filter(
            admin_payment_released=True
        ).aggregate(
            total=Sum('developer_payout_amount')
        )['total'] or 0
        
        pending_earnings = projects.filter(
            status='completed',
            admin_payment_released=False
        ).aggregate(
            total=Sum('developer_payout_amount')
        )['total'] or 0
        
        # Augment earnings by checking per-user assigned_payments mapping
        user = self.request.user
        extra_total = 0
        extra_pending = 0
        for p in projects:
            if p.admin_payment_released:
                extra_total += p.get_user_payout(user)
            elif p.status == 'completed' and not p.admin_payment_released:
                extra_pending += p.get_user_payout(user)

        context['total_earnings'] = (total_earnings or 0) + extra_total
        context['pending_earnings'] = (pending_earnings or 0) + extra_pending

        # Attach per-user payout value on each project so templates can show it without calling methods with args
        for p in context['assigned_projects']:
            p.user_payout = p.get_user_payout(user)
        for p in context['in_progress_projects']:
            p.user_payout = p.get_user_payout(user)
        for p in context['completed_projects']:
            p.user_payout = p.get_user_payout(user)

        return context

class DeveloperProjectDetailView(ProjectExecutionMixin, DetailView):
    """View for execution roles (developer, designer, seo, gbp) to see project details."""
    model = Project
    template_name = 'project_detail_developer.html'
    context_object_name = 'project'

    def get_queryset(self):
        # Allow access to the assigned developer or any member of the assigned team
        return Project.objects.filter(models.Q(assigned_to=self.request.user) | models.Q(assigned_team=self.request.user)).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['update_form'] = DeveloperUpdateForm(instance=self.object)
        # Provide user-specific payout amount for display in template
        context['user_payout'] = self.object.get_user_payout(self.request.user)
        return context


class DeveloperUpdateStatusView(ProjectExecutionMixin, UpdateView):
    """View for execution roles to update project status and add work.

    Enforces that only the role associated with a project's current stage may update status
    when relevant (e.g., developer stages can only be updated by users with developer role).
    """
    model = Project
    form_class = DeveloperUpdateForm
    template_name = 'developer_update.html'

    # Mapping of project stages to permitted roles
    STAGE_ROLE_MAP = {
        'design': ['designer'],
        'landing_dev': ['developer'],
        'full_dev': ['developer'],
        'deployment': ['developer'],
        'seo_gbp_ongoing': ['seo', 'gbp'],
    }

    def get_queryset(self):
        return Project.objects.filter(models.Q(assigned_to=self.request.user) | models.Q(assigned_team=self.request.user)).distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        # Provide project into template as 'project' and whether current user may change status
        context['project'] = project
        profile = getattr(self.request.user, 'profile', None)
        required_roles = self.STAGE_ROLE_MAP.get(project.current_stage, [])
        if required_roles and profile:
            context['can_update_status'] = any(profile.has_role(r) for r in required_roles)
        else:
            # If no specific role mapping, allow (default) — e.g., generic assigned -> allow team members
            context['can_update_status'] = True
        return context

    def form_valid(self, form):
        project = form.save(commit=False)

        # Enforce role-based permission when updating status
        profile = getattr(self.request.user, 'profile', None)
        required_roles = self.STAGE_ROLE_MAP.get(project.current_stage, [])
        if required_roles:
            allowed = False
            if profile and any(profile.has_role(r) for r in required_roles):
                allowed = True
            if not allowed:
                messages.error(self.request, 'You are not permitted to update the status for this stage.')
                return redirect('projects:developer_project_detail', pk=project.pk)

        if form.cleaned_data['status'] == 'completed':
            project.date_completed = timezone.now()
        # If developer clicked 'Submit for client approval' set appropriate client approval stage
        if self.request.POST.get('submit_for_client_approval'):
            if project.current_stage == 'landing_dev':
                project.current_stage = 'client_approval_landing'
            elif project.current_stage == 'full_dev':
                project.current_stage = 'client_approval_final'
            # keep status as in_progress until admin advances
            log_activity('submit_for_client_approval', 'project', project.id, self.request.user, note=form.cleaned_data.get('developer_notes'))
        project.save()
        # Include developer notes (if any) in activity log
        dev_note = form.cleaned_data.get('developer_notes')
        log_activity('developer_update', 'project', project.id, self.request.user, note=dev_note)
        messages.success(self.request, 'Project updated successfully!')
        return redirect('projects:developer_project_detail', pk=project.pk)


@login_required
def my_earnings(request):
    """Simple earnings overview for the logged-in user."""
    user = request.user
    total = 0
    pending = 0

    # Developer earnings
    from django.db.models import Sum
    dev_projects = Project.objects.filter(assigned_to=user)
    total += sum([p.get_user_payout(user) for p in dev_projects if p.admin_payment_released])
    pending += sum([p.get_user_payout(user) for p in dev_projects if p.status == 'completed' and not p.admin_payment_released])

    # Team assigned payouts (per-user mappings)
    team_projects = Project.objects.filter(assigned_team=user)
    total += sum([p.get_user_payout(user) for p in team_projects if p.admin_payment_released])
    pending += sum([p.get_user_payout(user) for p in team_projects if p.status == 'completed' and not p.admin_payment_released])

    # Fetcher earnings
    fetcher_projects = Project.objects.filter(created_by=user)
    total += sum([float(p.fetcher_commission_amount or 0) for p in fetcher_projects if p.admin_payment_released])
    pending += sum([float(p.fetcher_commission_amount or 0) for p in fetcher_projects if p.status == 'completed' and not p.admin_payment_released])

    # Additional role-based payouts for execution roles (designer, seo, gbp, social_media)
    profile = getattr(user, 'profile', None)
    if profile:
        # Designer
        if profile.has_role('designer'):
            designer_projects = Project.objects.filter(assigned_team=user)
            total += sum([float(p.designer_payout_amount or 0) for p in designer_projects if p.admin_payment_released])
            pending += sum([float(p.designer_payout_amount or 0) for p in designer_projects if p.status == 'completed' and not p.admin_payment_released])
        # SEO
        if profile.has_role('seo'):
            seo_projects = Project.objects.filter(assigned_team=user)
            total += sum([float(p.seo_payout_amount or 0) for p in seo_projects if p.admin_payment_released])
            pending += sum([float(p.seo_payout_amount or 0) for p in seo_projects if p.status == 'completed' and not p.admin_payment_released])
        # GBP
        if profile.has_role('gbp'):
            gbp_projects = Project.objects.filter(assigned_team=user)
            total += sum([float(p.gbp_payout_amount or 0) for p in gbp_projects if p.admin_payment_released])
            pending += sum([float(p.gbp_payout_amount or 0) for p in gbp_projects if p.status == 'completed' and not p.admin_payment_released])
        # Social Media
        if profile.has_role('social_media'):
            social_projects = Project.objects.filter(assigned_team=user)
            total += sum([float(p.social_media_payout_amount or 0) for p in social_projects if p.admin_payment_released])
            pending += sum([float(p.social_media_payout_amount or 0) for p in social_projects if p.status == 'completed' and not p.admin_payment_released])

    return render(request, 'my_earnings.html', {'total': total, 'pending': pending})


@login_required
def execution_submit_update(request, pk):
    """Allows execution team members (designer, developer, seo, gbp) to submit updates for assigned projects."""
    project = get_object_or_404(Project, pk=pk)
    profile = request.user.profile

    # Check role and assignment
    if not (profile.has_role('designer') or profile.has_role('developer') or profile.has_role('seo') or profile.has_role('gbp')):
        messages.error(request, 'You do not have permission to add updates.')
        return redirect('dashboard:execution_dashboard')

    if request.user not in project.assigned_team.all() and request.user != project.assigned_to:
        messages.error(request, 'You are not assigned to this project.')
        return redirect('dashboard:execution_dashboard')

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        links = request.POST.get('links', '').strip()
        if not message:
            messages.error(request, 'Please provide an update message.')
            return redirect('projects:developer_project_detail', pk=project.pk)
        # Save the message as an activity note as well
        log_activity('project_update', 'project', project.id, request.user, note=message)
        messages.success(request, 'Update submitted.')
        return redirect('projects:developer_project_detail', pk=project.pk)

    return redirect('dashboard:execution_dashboard')
