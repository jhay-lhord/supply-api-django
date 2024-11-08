from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        post_migrate.connect(run_create_groups, sender=self)
        post_migrate.connect(run_create_super_admin_user, sender=self)


def run_create_groups(sender, **kwargs):
    from .groups import create_groups
    create_groups()

def run_create_super_admin_user(sender, **kwargs):
    from .super_admin import create_super_admin_user
    create_super_admin_user()
