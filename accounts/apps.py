from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Register a post_migrate handler to create default roles after migrations
        from django.db.models.signals import post_migrate
        from django.apps import apps

        def create_default_roles(sender, **kwargs):
            Role = apps.get_model('accounts', 'Role')
            default_roles = ['cold_caller', 'sales_closer', 'designer', 'developer', 'seo', 'gbp', 'project_manager', 'client', 'admin']
            for r in default_roles:
                Role.objects.get_or_create(name=r)

        post_migrate.connect(create_default_roles, sender=self)

