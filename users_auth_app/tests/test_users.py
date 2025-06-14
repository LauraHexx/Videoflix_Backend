
import pytest
import uuid
from users_auth_app.models import CustomUser
from users_auth_app.api.backends import VerifiedEmailBackend
from utils.test_utils import create_verified_user, create_unverified_user, create_regular_user, create_superuser


@pytest.mark.django_db
def test_create_user_successfully():
    """Test creating a user with email and password."""
    user = create_regular_user()
    assert user.email == "user@example.com"
    assert user.username == "testuser"
    assert user.check_password("securepass123")
    assert user.is_active


@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    """Test creating a user without email raises ValueError."""
    with pytest.raises(ValueError):
        CustomUser.objects.create_user(email=None, password="abc123")


@pytest.mark.django_db
def test_create_superuser_successfully():
    """Test creating a superuser sets is_staff and is_superuser."""
    admin = create_superuser()
    assert admin.is_staff
    assert admin.is_superuser


@pytest.mark.django_db
def test_create_superuser_with_false_flags_raises_error():
    """Test creating superuser with is_staff or is_superuser False raises error."""
    with pytest.raises(ValueError):
        create_superuser(is_staff=False)

    with pytest.raises(ValueError):
        create_superuser(is_superuser=False)


@pytest.mark.django_db
def test_verification_token_auto_assigned():
    """Test a new user gets a UUID verification token."""
    user = create_regular_user()
    assert user.verification_token is not None
    assert isinstance(user.verification_token, uuid.UUID)


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
