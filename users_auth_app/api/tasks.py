import ssl
import uuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from users_auth_app.models import CustomUser


# def send_verification_email_task(user_id: int) -> None:
#    """
#    Sends a verification email with token link to the user.
#    Token is saved in user model and included in the confirmation URL.
#    Uses a custom SSL context for secure email sending.
#    """
#    user = CustomUser.objects.get(pk=user_id)
#
#    # generate and save token
#    token = str(uuid.uuid4())
#    user.verification_token = token
#    user.save(update_fields=["verification_token"])
#
#    # build verification link
#    backend_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
#    verification_link = f"{backend_url}/api/registration/verify/{token}/"
#
#    # render HTML email
#    html_content = render_to_string("users_auth_app/confirm_email.html", {
#        "user": user,
#        "verification_link": verification_link,
#    })
#
#    # SSL-Kontext ohne Zertifikatsprüfung (unsicher, nur temporär!)
#    ssl_context = ssl._create_unverified_context()
#
#    # get custom email connection with this unverified SSL context
#    connection = get_connection(
#        fail_silently=False,
#        ssl_context=ssl_context,
#        host=settings.EMAIL_HOST,
#        port=settings.EMAIL_PORT,
#        username=settings.EMAIL_HOST_USER,
#        password=settings.EMAIL_HOST_PASSWORD,
#        use_tls=settings.EMAIL_USE_TLS,
#        use_ssl=settings.EMAIL_USE_SSL,
#    )
#
#    # create email message
#    msg = EmailMultiAlternatives(
#        subject="Verify your email address",
#        body="",
#        from_email=settings.DEFAULT_FROM_EMAIL,
#        to=[user.email],
#        connection=connection,
#    )
#    msg.attach_alternative(html_content, "text/html")
#    msg.send()


def send_verification_email_task(user_id: int) -> None:
    """
    Sends a verification email with token link to the user.
    Token is saved in user model and included in the confirmation URL.
    Uses Django's default email backend with TLS.
    """
    user = CustomUser.objects.get(pk=user_id)

    # generate and save token
    token = str(uuid.uuid4())
    user.verification_token = token
    user.save(update_fields=["verification_token"])

    # build verification link
    backend_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
    verification_link = f"{backend_url}/api/registration/verify/{token}/"

    # render HTML email
    html_content = render_to_string("users_auth_app/confirm_email.html", {
        "user": user,
        "verification_link": verification_link,
    })

    # get email connection (ohne ssl_context!)
    connection = get_connection(
        fail_silently=False,
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER,
        password=settings.EMAIL_HOST_PASSWORD,
        use_tls=settings.EMAIL_USE_TLS,
        use_ssl=settings.EMAIL_USE_SSL,
    )

    # create email message
    msg = EmailMultiAlternatives(
        subject="Verify your email address",
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
        connection=connection,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
