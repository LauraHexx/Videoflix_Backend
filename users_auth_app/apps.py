from django.apps import AppConfig


class UsersAuthAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users_auth_app'

    # def ready(self):
    #    from users_auth_app.api import signals
