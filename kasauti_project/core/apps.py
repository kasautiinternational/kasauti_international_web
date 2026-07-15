from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'KASAUTI Core'

    def ready(self):
        # NEW: order alert signals load karo
        from . import signals  # noqa: F401