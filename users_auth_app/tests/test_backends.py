
from utils.test_utils import create_verified_user, create_unverified_user
from users_auth_app.api.backends import VerifiedEmailBackend
import pytest
from django.contrib.auth import get_user_model
User = get_user_model()


@pytest.mark.django_db
def test_authenticate_success():
    """Authenticate returns user if email, password and is_verified are correct."""
    user, password = create_verified_user()
    backend = VerifiedEmailBackend()
    authenticated_user = backend.authenticate(
        request=None, email=user.email, password=password)

    assert authenticated_user == user


@pytest.mark.django_db
def test_authenticate_wrong_email():
    """Authenticate returns None if email does not exist."""
    backend = VerifiedEmailBackend()
    authenticated_user = backend.authenticate(
        request=None, email="wrong@example.com", password="secret123")
    assert authenticated_user is None


@pytest.mark.django_db
def test_authenticate_wrong_password():
    """Authenticate returns None if password is wrong."""
    user, _ = create_verified_user()
    backend = VerifiedEmailBackend()
    authenticated_user = backend.authenticate(
        request=None, email=user.email, password="wrongpass")

    assert authenticated_user is None


@pytest.mark.django_db
def test_authenticate_not_verified():
    """Authenticate returns None if user is not verified."""
    user, password = create_unverified_user()
    backend = VerifiedEmailBackend()
    authenticated_user = backend.authenticate(
        request=None, email=user.email, password=password)

    assert authenticated_user is None
