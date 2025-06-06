import uuid
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from users_auth_app.models import CustomUser


def send_verification_email_task(user_id):
    """
    Sends a verification email with a token link to the user.

    The email includes a link to the backend verification endpoint.
    """
    user = CustomUser.objects.get(pk=user_id)

    # Generate a new verification token
    token = str(uuid.uuid4())

    # Store token in user model
    user.verification_token = token
    user.save()

    # Build verification URL (Backend endpoint!)
    backend_url = getattr(settings, "BACKEND_URL", "http://localhost:8000")
    verification_link = f"{backend_url}/api/registration/verify/{token}/"

    # Render email template with token link
    html_content = render_to_string("users_auth_app/confirm_email.html", {
        "user": user,
        "verification_link": verification_link,
    })

    # Prepare and send the email
    subject = "Verify your email address"
    msg = EmailMultiAlternatives(
        subject, "", settings.DEFAULT_FROM_EMAIL, [user.email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
