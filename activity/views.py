from django.shortcuts import render
from .models import ActivityLog
from accounts.mixins import AdminRequiredMixin
from django.contrib.auth.decorators import user_passes_test


@user_passes_test(lambda u: hasattr(u, 'profile') and (u.profile.has_role('admin') or u.profile.has_role('project_manager')))
def activity_logs(request):
    logs = ActivityLog.objects.all()[:200]
    return render(request, 'activity_logs.html', {'logs': logs})


def can_view_project_logs(user, project_id):
    # Admins can always view; others must be part of the project team or creator
    try:
        from projects.models import Project
        project = Project.objects.get(pk=project_id)
    except Exception:
        return False
    if (
        user.is_superuser
        or (
            hasattr(user, 'profile')
            and (
                user.profile.has_role('admin')
                or user.profile.has_role('project_manager')
            )
        )
    ):
        return True
    if user == project.created_by or user == project.assigned_to or user in project.assigned_team.all():
        return True
    return False


def activity_logs_for_project(request, pk):
    if not can_view_project_logs(request.user, pk):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('You do not have permission to view these logs.')

    # Fetch ActivityLog entries for this project
    activity_logs = list(ActivityLog.objects.filter(entity_type='project', entity_id=pk)[:500])

    # Also include ProjectUpdate entries so developers' notes appear in project activity
    from projects.models import ProjectUpdate
    updates = list(ProjectUpdate.objects.filter(project_id=pk)[:500])

    # Normalize entries into a common structure and merge-sort by timestamp descending
    normalized = []
    for a in activity_logs:
        normalized.append({'timestamp': a.timestamp, 'actor': a.performed_by, 'action': a.action, 'note': a.note})
    for u in updates:
        normalized.append({'timestamp': u.created_at, 'actor': u.user, 'action': 'project_update', 'note': u.message})

    # Sort by timestamp desc
    normalized.sort(key=lambda x: x['timestamp'], reverse=True)

    return render(request, 'activity_logs_project.html', {'logs': normalized, 'project_id': pk})
