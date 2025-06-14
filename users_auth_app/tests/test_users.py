
import pytest
import uuid
from users_auth_app.models import CustomUser


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
