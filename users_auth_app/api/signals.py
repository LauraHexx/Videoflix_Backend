from utils.export_utils import export_model_to_s3
from users_auth_app.api.tasks import send_verification_email_task
import django_rq
from users_auth_app.models import CustomUser
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete


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


@receiver(post_save, sender=CustomUser)
def export_customuser_on_update(sender, instance, created, **kwargs):
    """Export CustomUser data after create or update."""
    if not created:
        export_model_to_s3(CustomUser)


@receiver(post_delete, sender=CustomUser)
def export_customuser_on_delete(sender, instance, **kwargs):
    """Export CustomUser data after deletion."""
    export_model_to_s3(CustomUser)
