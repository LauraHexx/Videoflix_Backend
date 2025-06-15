import ssl
import uuid
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from users_auth_app.models import CustomUser


def send_verification_email_task(user_id: int) -> None:
    """
    Sends a verification email with token link to the user.
    Token is saved in user model and included in the confirmation URL.
    Uses Django's email backend with custom TLS connection.
    """
    print(f"[INFO] Sending verification email to user ID: {user_id}")

    try:
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        print(f"[WARNING] User with ID {user_id} does not exist.")
        return

    token = str(uuid.uuid4())
    user.verification_token = token
    user.save(update_fields=["verification_token"])
    print(f"[INFO] Saved verification token for user {user.email}: {token}")

    backend_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
    verification_link = f"{backend_url}/api/registration/verify/{token}/"
    print(f"[INFO] Generated verification link: {verification_link}")

    html_content = render_to_string("users_auth_app/confirm_email.html", {
        "user": user,
        "verification_link": verification_link,
    })
    print(f"[INFO] Rendered HTML email content.")

    try:
        connection = get_connection(
            fail_silently=False,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=settings.EMAIL_USE_SSL,
        )
        print(
            f"[INFO] Email connection established with host: {settings.EMAIL_HOST}")
    except Exception as e:
        print(f"[ERROR] Failed to establish SMTP connection: {e}")
        return

    msg = EmailMultiAlternatives(
        subject="Verify your email address",
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
        connection=connection,
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        print(f"[SUCCESS] Verification email sent to {user.email}")
    except Exception as e:
        print(f"[ERROR] Email send error for user {user_id}: {e}")
