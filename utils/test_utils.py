from django.contrib.auth import get_user_model
from users_auth_app.models import CustomUser


User = get_user_model()


def create_verified_user(email="user@example.com", password="testpass123"):
    """Create and return a verified user and its password."""
    user = User.objects.create_user(
        email=email, password=password, is_verified=True)
    return user, password


def create_unverified_user(email="user2@example.com", password="testpass123"):
    """Create and return an unverified user and its password."""
    user = User.objects.create_user(
        email=email, password=password, is_verified=False)
    return user, password


def create_regular_user(email="user@example.com", password="securepass123", username="testuser"):
    """Creates a standard user with default or provided values."""
    return CustomUser.objects.create_user(
        email=email,
        password=password,
        username=username
    )


def create_superuser(email="admin@example.com", password="adminpass", **extra_fields):
    """Creates a superuser with optional override flags like is_staff or is_superuser."""
    return CustomUser.objects.create_superuser(
        email=email,
        password=password,
        **extra_fields
    )
