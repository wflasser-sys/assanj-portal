"""
Dashboard views with role-based routing.
Redirects users to their appropriate dashboard based on role.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache


@login_required
def dashboard_router(request):
    """
    Main dashboard router.
    Redirects user to appropriate dashboard based on their role.
    """
    # Allow users linked as client to proceed even if a profile is missing
    if not hasattr(request.user, 'profile') and not hasattr(request.user, 'client'):
        messages.error(request, 'User profile not found. Please contact admin.')
        return redirect('accounts:login')
    
    profile = getattr(request.user, 'profile', None)

    # Admin / Project Manager -> Admin dashboard
    if profile and (profile.has_role('admin') or profile.has_role('project_manager')):
        return redirect('projects:admin_projects')

    # Cold Caller -> Cold Caller Dashboard
    if profile and profile.has_role('cold_caller'):
        return redirect('leads:cold_caller_dashboard')

    # Sales Closer -> Sales Closer Dashboard
    if profile and profile.has_role('sales_closer'):
        return redirect('leads:sales_closer_dashboard')

    # Execution roles -> Execution Dashboard
    if profile and (profile.has_role('designer') or profile.has_role('developer') or profile.has_role('seo') or profile.has_role('gbp')):
        return redirect('dashboard:execution_dashboard')

    # Client -> Client Dashboard
    # Support users who are linked to a Client object even if their profile lacks the role
    if (profile and profile.has_role('client')) or hasattr(request.user, 'client'):
        return redirect('dashboard:client_dashboard')

    messages.error(request, 'Invalid user role. Please contact admin.')
    return redirect('accounts:login')

@login_required
def fetcher_dashboard(request):
    """
    Fetcher dashboard showing quick actions and project summary.
    """
    if not hasattr(request.user, 'profile') or not request.user.profile.has_role('cold_caller'):
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    from projects.models import Project
    from clients.models import Client
    from django.db.models import Sum, Q
    
    projects = Project.objects.filter(created_by=request.user)
    clients = Client.objects.filter(created_by=request.user)
    
    # Cache earnings calculations - 5 minute cache per user
    cache_key = f'fetcher_earnings_{request.user.id}'
    cached_earnings = cache.get(cache_key)
    
    if cached_earnings:
        total_earnings = cached_earnings['total_earnings']
        pending_earnings = cached_earnings['pending_earnings']
    else:
        # Calculate earnings
        total_earnings = projects.filter(
            admin_payment_released=True
        ).aggregate(
            total=Sum('fetcher_commission_amount')
        )['total'] or 0
        
        pending_earnings = projects.filter(
            status='completed',
            admin_payment_released=False
        ).aggregate(
            total=Sum('fetcher_commission_amount')
        )['total'] or 0
        
        cache.set(cache_key, {
            'total_earnings': total_earnings,
            'pending_earnings': pending_earnings,
        }, 300)  # 5 minutes
    
    context = {
        'total_projects': projects.count(),
        'new_projects': projects.filter(status='new').count(),
        'in_progress_projects': projects.filter(status__in=['assigned', 'in_progress']).count(),
        'completed_projects': projects.filter(status__in=['completed', 'payment_done']).count(),
        'total_clients': clients.count(),
        'recent_projects': projects[:5],
        'recent_clients': clients[:5],
        # NEW: Earnings data
        'total_earnings': total_earnings,
        'pending_earnings': pending_earnings,
    }
    
    return render(request, 'dashboard_fetcher.html', context)


@login_required
def cold_caller_redirect(request):
    # Redirect to the cold caller dashboard in the leads app
    return redirect('leads:cold_caller_dashboard')


@login_required
def execution_dashboard(request):
    # Show only projects assigned to the current execution user
    from projects.models import Project
    user = request.user
    
    # Cache execution projects per user - 3 minute cache
    cache_key = f'execution_projects_{user.id}'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        projects = cached_data['projects']
        completed_projects = cached_data['completed_projects']
        ongoing_projects = cached_data['ongoing_projects']
    else:
        projects = Project.objects.filter(assigned_team=user) | Project.objects.filter(assigned_to=user)
        projects = projects.distinct()
        
        # Separate completed and ongoing projects
        completed_projects = projects.filter(status__in=['completed', 'payment_done']).order_by('-date_completed')
        ongoing_projects = projects.filter(status__in=['new', 'assigned', 'in_progress']).order_by('-date_assigned')
        
        cache.set(cache_key, {
            'projects': projects,
            'completed_projects': list(completed_projects),
            'ongoing_projects': list(ongoing_projects),
        }, 180)  # 3 minutes
    
    return render(request, 'dashboard_execution.html', {
        'projects': projects,
        'completed_projects': completed_projects,
        'ongoing_projects': ongoing_projects
    })


@login_required
def client_dashboard(request):
    """Client dashboard — shows projects, recent updates and activity logs."""
    from projects.models import Project, ProjectUpdate
    from activity.models import ActivityLog

    # Allow admins to view client dashboard for debugging, else ensure user is a client
    if not (hasattr(request.user, 'client') or (hasattr(request.user, 'profile') and request.user.profile.has_role('client'))):
        messages.error(request, 'You are not registered as a client.')
        return redirect('dashboard:dashboard')

    # Safely obtain Client; if a profile says 'client' but no Client record exists,
    # show a helpful message and avoid throwing RelatedObjectDoesNotExist.
    try:
        client = request.user.client
    except Exception:
        messages.error(request, 'A client record is not linked to your account. Please contact support.')
        return redirect('dashboard:dashboard')

    projects = Project.objects.filter(client=client)

    # Cache recent updates and logs per project - 2 minute cache
    for p in projects:
        # Cache key for each project's updates
        cache_key_updates = f'project_{p.id}_updates'
        cached_updates = cache.get(cache_key_updates)
        
        if cached_updates:
            p.recent_updates = cached_updates
        else:
            p.recent_updates = list(ProjectUpdate.objects.filter(project=p).order_by('-created_at')[:5])
            cache.set(cache_key_updates, p.recent_updates, 120)  # 2 minutes
        
        # Cache key for each project's logs
        cache_key_logs = f'project_{p.id}_logs'
        cached_logs = cache.get(cache_key_logs)
        
        if cached_logs:
            p.recent_logs = cached_logs
        else:
            p.recent_logs = list(ActivityLog.objects.filter(entity_type='project', entity_id=p.id).order_by('-timestamp')[:10])
            cache.set(cache_key_logs, p.recent_logs, 120)  # 2 minutes

    context = {
        'projects': projects,
    }

    return render(request, 'dashboard_client.html', context)


@login_required
def my_projects(request):
    """My Projects view for project managers and closers to see projects they created."""
    profile = getattr(request.user, 'profile', None)
    
    # Allow project_manager and sales_closer to see their created projects
    if not (profile and (profile.has_role('project_manager') or profile.has_role('sales_closer') or profile.has_role('cold_caller'))):
        messages.error(request, 'Access denied.')
        return redirect('dashboard:dashboard')
    
    from projects.models import Project
    
    # Get all projects created by this user
    projects = Project.objects.filter(created_by=request.user).select_related('client', 'assigned_to').prefetch_related('assigned_team')
    
    context = {
        'projects': projects,
        'total_projects': projects.count(),
        'new_projects': projects.filter(status='new').count(),
        'assigned_projects': projects.filter(status='assigned').count(),
        'in_progress_projects': projects.filter(status__in=['in_progress']).count(),
        'completed_projects': projects.filter(status='completed').count(),
    }
    
    return render(request, 'my_projects.html', context)
