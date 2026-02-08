def user_profile(request):
    """Provide a safe reference to the user's profile (or None) and role flags for templates.

    Adds `user_profile`, `user_roles` (list) and convenience booleans such as
    `is_fetcher`, `is_admin`, `is_client` so templates don't need to call
    methods or access attributes that may not exist.
    """
    profile = None
    roles = []
    flags = {
        'is_cold_caller': False,
        'is_admin': False,
        'is_developer': False,
        'is_client': False,
        'is_sales_closer': False,
        'is_project_manager': False,
    }

    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        try:
            profile = user.profile
            roles = [r.name for r in profile.roles.all()]
            flags['is_cold_caller'] = 'cold_caller' in roles
            flags['is_admin'] = 'admin' in roles
            flags['is_developer'] = 'developer' in roles
            flags['is_client'] = 'client' in roles
            flags['is_sales_closer'] = 'sales_closer' in roles
            flags['is_project_manager'] = 'project_manager' in roles
        except Exception:
            profile = None

    context = {'user_profile': profile, 'user_roles': roles}
    context.update(flags)
    return context
