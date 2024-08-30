from django.apps import AppConfig

# from .tasks import process


class TrendsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trends"

    # def ready(self):
    #     pass
        # from trends.tasks import process

        # process()
