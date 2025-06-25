from django.db.models.signals import post_save
from users_auth_app.models import CustomUser
from users_auth_app.api.signals import send_email_on_user_create


def pytest_runtest_setup(item):
    """
    Disconnect the send_email_on_user_create signal from CustomUser post_save
    to prevent email sending during tests.
    """
    post_save.disconnect(send_email_on_user_create, sender=CustomUser)
