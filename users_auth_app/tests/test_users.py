
from utils.test_utils import create_regular_user, create_superuser
from users_auth_app.models import CustomUser
import pytest
import uuid
from django.contrib.auth import get_user_model
User = get_user_model()


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
def test_create_user_success():
    """Test creating a normal user with valid email and password."""
    manager = User.objects
    email = "testuser@example.com"
    password = "securepassword"
    username = "testuser"

    user = manager.create_user(
        email=email, password=password, username=username)

    assert user.email == email.lower()
    assert user.username == username
    assert user.check_password(password)
    assert not user.is_staff
    assert not user.is_superuser


def test_create_user_no_email_raises():
    """Test creating user without email raises ValueError."""
    manager = User.objects
    with pytest.raises(ValueError, match="The Email must be set"):
        manager.create_user(email=None, password="pass123")


@pytest.mark.django_db
def test_create_superuser_success():
    """Test creating a superuser with correct flags."""
    manager = User.objects
    email = "admin@example.com"
    password = "supersecure"

    superuser = manager.create_superuser(email=email, password=password)

    assert superuser.email == email.lower()
    assert superuser.is_staff is True
    assert superuser.is_superuser is True
    assert superuser.check_password(password)


def test_create_superuser_is_staff_false_raises():
    """Test superuser creation fails if is_staff is False."""
    manager = User.objects
    with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
        manager.create_superuser(
            email="admin@example.com",
            password="pass",
            is_staff=False,
        )


def test_create_superuser_is_superuser_false_raises():
    """Test superuser creation fails if is_superuser is False."""
    manager = User.objects
    with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
        manager.create_superuser(
            email="admin@example.com",
            password="pass",
            is_superuser=False,
        )
