from django.db.models.signals import post_save
from users_auth_app.models import CustomUser
from users_auth_app.api.signals import send_email_on_user_create


def pytest_runtest_setup(item):
    post_save.disconnect(send_email_on_user_create, sender=CustomUser)
