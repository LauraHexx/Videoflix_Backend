from django.db.models.signals import post_save
from users_auth_app.models import CustomUser
from users_auth_app.api.signals import send_email_on_user_create
from video_flix_app.models import Video, UserWatchHistory
from video_flix_app.api.signals import enqueue_video_processing, enqueue_video_deletion, export_video_on_save, export_userwatchhistory_hourly


def pytest_runtest_setup(item):
    """
    Disable specific post_save signals before each pytest test run
    to prevent side effects during testing.
    """
    post_save.disconnect(send_email_on_user_create, sender=CustomUser)
    post_save.disconnect(enqueue_video_processing, sender=Video)
    post_save.disconnect(enqueue_video_deletion, sender=Video)
    post_save.disconnect(export_video_on_save, sender=Video)
    post_save.disconnect(export_userwatchhistory_hourly,
                         sender=UserWatchHistory)
