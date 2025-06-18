import uuid
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from users_auth_app.models import CustomUser


def get_user_by_id(user_id: int):
    """Retrieve user by ID or return None if not found."""
    try:
        return CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return None


def generate_verification_token() -> str:
    """Generate a new UUID4 token as string."""
    return str(uuid.uuid4())


def save_verification_token(user, token: str) -> None:
    """Save the verification token to the user model."""
    user.verification_token = token
    user.save(update_fields=["verification_token"])


def build_verification_link(token: str) -> str:
    """Build the full verification URL with token."""
    backend_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
    return f"{backend_url}/api/registration/verify/{token}/"


def render_email_html(user, verification_link: str) -> str:
    """Render the HTML content for the verification email."""
    return render_to_string("users_auth_app/confirm_email.html", {
        "user": user,
        "verification_link": verification_link,
    })


def get_email_connection():
    """Establish SMTP connection with email settings."""
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
        return connection
    except Exception as e:
        print(f"[ERROR] Failed to establish SMTP connection: {e}")
        return None


def send_email(user_email: str, html_content: str, connection) -> None:
    """Send the verification email via the given SMTP connection."""
    if not connection:
        return

    msg = EmailMultiAlternatives(
        subject="Confirm your email",
        body="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email],
        connection=connection,
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        print(f"[SUCCESS] Email sent to {user_email}")
    except Exception as e:
        print(f"[ERROR] Email send error for user {user_email}: {e}")


def send_verification_email_task(user_id: int) -> None:
    """Main task: orchestrates sending the verification email to the user."""
    user = get_user_by_id(user_id)
    if not user:
        return

    token = generate_verification_token()
    save_verification_token(user, token)

    verification_link = build_verification_link(token)
    html_content = render_email_html(user, verification_link)

    connection = get_email_connection()
    send_email(user.email, html_content, connection)


def build_password_reset_link(token: str) -> str:
    """Build the full frontend URL for password reset with token."""
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
    full_link = f"{frontend_url}/reset-password/{token}/"
    return full_link


def render_password_reset_email_html(reset_link: str) -> str:
    """Render HTML content for the password reset email."""
    html = render_to_string("users_auth_app/reset_password.html", {
        "reset_link": reset_link,
    })
    return html


def send_password_reset_email_task(user_id: int) -> None:
    """Sends a password reset email using shared helper functions."""
    user = get_user_by_id(user_id)
    if not user:
        return

    reset_link = build_password_reset_link(user.verification_token)
    html_content = render_password_reset_email_html(reset_link)

    connection = get_email_connection()

    send_email(user.email, html_content, connection)
