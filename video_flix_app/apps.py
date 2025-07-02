from django.apps import AppConfig


class VideoFlixAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_flix_app'

    def ready(self):
        import video_flix_app.api.signals
        from video_flix_app.api.scheduler import register_watchhistory_export_job
        register_watchhistory_export_job()
