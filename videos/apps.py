from django.apps import AppConfig


class VideosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'videos'
    verbose_name = '🎬 مكتبة الفيديوهات'

    def ready(self):
        from . import signals  # noqa: F401
