from django.apps import AppConfig

# from .tasks import start_trending_scheduler


class TrendsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trends"

    def ready(self):
        from trends.tasks import start_trending_scheduler

        start_trending_scheduler()
