"""
Cache utility functions for project-related views.
Handles cache invalidation when projects are modified.
"""

from django.core.cache import cache


def invalidate_admin_cache():
    """Invalidate admin dashboard caches."""
    cache.delete('admin_projects_status_counts')
    cache.delete('admin_leads_overview')
    cache.delete('admin_agency_earnings')


def invalidate_developer_cache(developer_id):
    """Invalidate developer cache."""
    cache.delete('admin_developers_list')


def invalidate_client_project_cache(project_id):
    """Invalidate client dashboard caches for a specific project."""
    cache.delete(f'project_{project_id}_updates')
    cache.delete(f'project_{project_id}_logs')


def invalidate_user_fetcher_cache(user_id):
    """Invalidate fetcher dashboard cache for a specific user."""
    cache.delete(f'fetcher_earnings_{user_id}')


def invalidate_user_execution_cache(user_id):
    """Invalidate execution dashboard cache for a specific user."""
    cache.delete(f'execution_projects_{user_id}')


def invalidate_all_user_caches(user_id):
    """Invalidate all caches for a specific user."""
    invalidate_user_fetcher_cache(user_id)
    invalidate_user_execution_cache(user_id)


def invalidate_project_caches(project_id, user_id=None):
    """Invalidate all caches related to a project."""
    invalidate_admin_cache()
    invalidate_client_project_cache(project_id)
    if user_id:
        invalidate_all_user_caches(user_id)
