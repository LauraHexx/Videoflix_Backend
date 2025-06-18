from django.db.models.signals import post_save
from django.dispatch import receiver
from users_auth_app.models import CustomUser
import django_rq
from users_auth_app.api.tasks import send_verification_email_task


@receiver(post_save, sender=CustomUser)
def send_email_on_user_create(sender, instance, created, **kwargs) -> None:
    """
    Enqueues email verification task for newly created users (not verifed),
    except when the first superuser is created.
    """
    if instance.is_verified:
        return

    # Prevent sending email if this is the very first user and a superuser
    if CustomUser.objects.count() == 1 and instance.is_superuser:
        return

    queue = django_rq.get_queue("default")
    queue.enqueue(send_verification_email_task, instance.pk)
