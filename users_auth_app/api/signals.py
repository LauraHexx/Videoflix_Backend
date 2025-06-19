from django.db.models.signals import post_save
from django.dispatch import receiver
from users_auth_app.models import CustomUser
import django_rq
from users_auth_app.api.tasks import send_verification_email_task


@receiver(post_save, sender=CustomUser)
def send_email_on_user_create(sender, instance, created, **kwargs):
    """
    Enqueue verification email if:
    - User is newly created and not verified, or
    - User is updated (not verified) and password was changed.
    Never send for any superuser.
    """
    if instance.is_verified or instance.is_superuser:
        return

    update_fields = kwargs.get("update_fields")
    if created or (update_fields and "password" in update_fields):
        queue = django_rq.get_queue("default")
        queue.enqueue(send_verification_email_task, instance.pk)
