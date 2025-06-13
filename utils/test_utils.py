import pytest
from django.contrib.auth import get_user_model


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
