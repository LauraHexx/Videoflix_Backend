import pytest
from rest_framework.test import APIClient
from users_auth_app.models import CustomUser
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.test import override_settings
from uuid import uuid4
from unittest.mock import patch, MagicMock
from django_rq import get_queue


from utils.test_utils import create_unverified_user
from users_auth_app.api.signals import send_email_on_user_create
from users_auth_app.api.tasks import send_verification_email_task


@pytest.fixture
def api_client():
    """Return DRF APIClient instance for request simulation."""
    return APIClient()


def register(
    api_client,
    email: str = "laura@example.com",
    password: str = "SuperSecure123",
    repeated_password: str = None,
):
    """
    Perform registration POST request with default or custom credentials.
    """
    url = "/api/registration/"
    return api_client.post(url, {
        "email": email,
        "password": password,
        "repeated_password": repeated_password or password,
    })


def verify_email(api_client, token):
    """
    Perform email verification GET request using token.
    """
    url = f"/api/registration/verify/{token}/"
    return api_client.get(url)


def send_email_on_user_create(sender, instance, created, **kwargs):
    """
    Signal handler to enqueue verification email task only once per new user,
    excluding verified users and the first superuser.
    """
    if not created:
        return

    if instance.is_verified:
        return

    superuser_count = CustomUser.objects.filter(
        is_superuser=True).exclude(pk=instance.pk).count()
    if instance.is_superuser and superuser_count == 0:
        return

    queue = get_queue()
    queue.enqueue(send_verification_email_task, instance.pk)


@pytest.mark.django_db
@patch("users_auth_app.api.signals.django_rq.get_queue")
def test_registration_success(mock_get_queue, api_client):
    """
    Test successful registration without triggering Redis queue.
    Ensures token is returned, user is created, and is_verified is False.
    """
    # Simulate Redis queue with mock
    mock_queue = mock_get_queue.return_value
    mock_queue.enqueue.return_value = None
    response = register(api_client)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "token" in data
    assert "user_id" in data
    assert data["email"] == "laura@example.com"
    user = CustomUser.objects.get(email="laura@example.com")
    assert Token.objects.filter(user=user).exists()
    assert user.is_verified is False


@pytest.mark.django_db
@patch("users_auth_app.api.signals.django_rq.get_queue")
def test_registration_user_already_exists(mock_get_queue, api_client):
    """
    Test registration fails if a user with the same email already exists.
    Redis queue is mocked to avoid real Redis connection.
    """
    mock_queue = mock_get_queue.return_value
    mock_queue.enqueue.return_value = None
    response_1 = register(api_client)
    assert response_1.status_code == status.HTTP_201_CREATED
    response_2 = register(api_client)
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    data = response_2.json()
    assert "email" in data
    assert "already exists" in str(data["email"]).lower()


@pytest.mark.django_db
def test_registration_password_mismatch(api_client):
    """Test registration fails if passwords do not match."""
    response = register(api_client, password="pass1",
                        repeated_password="pass2")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Passwords do not match." in str(response.content)


@pytest.mark.django_db
def test_registration_missing_fields(api_client):
    """Test registration fails if fields are missing."""
    url = "/api/registration/"
    response = api_client.post(url, {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "email" in data
    assert "password" in data
    assert "repeated_password" in data


@pytest.mark.django_db
@patch("users_auth_app.api.signals.django_rq.get_queue")
@override_settings(FRONTEND_URL="http://testfrontend.com")
def test_verify_email_success(mock_get_queue, api_client):
    """
    Test valid email verification token activates user and redirects.
    Erstellt explizit einen Token für den User.
    """
    mock_queue = mock_get_queue.return_value
    mock_queue.enqueue.return_value = None
    user, _ = create_unverified_user()
    Token.objects.get_or_create(user=user)
    token = user.verification_token
    response = verify_email(api_client, token)
    user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == "http://testfrontend.com/login"
    assert user.is_verified is True
    assert user.verification_token is None


@pytest.mark.django_db
@patch("users_auth_app.api.signals.django_rq.get_queue")
def test_verify_email_invalid_token(mock_get_queue, api_client):
    """Test invalid email verification token returns 400."""
    mock_queue = mock_get_queue.return_value
    mock_queue.enqueue.return_value = None
    fake_token = str(uuid4())
    response = verify_email(api_client, fake_token)
    assert response.status_code == 400


@pytest.mark.django_db
@patch("django_rq.get_queue")
def test_no_enqueue_for_verified_user(mock_get_queue):
    """
    Ensure no enqueue call is made when the user is already verified.
    """
    mock_queue = MagicMock()
    mock_get_queue.return_value = mock_queue

    user = CustomUser.objects.create(
        email="verified@example.com", is_verified=True)
    send_email_on_user_create(sender=CustomUser, instance=user, created=True)

    mock_queue.enqueue.assert_not_called()


@pytest.mark.django_db
@patch("django_rq.get_queue")
def test_no_enqueue_for_first_superuser(mock_get_queue):
    """
    Ensure no enqueue call is made when the first superuser is created.
    """
    mock_queue = MagicMock()
    mock_get_queue.return_value = mock_queue

    user = CustomUser.objects.create(
        email="admin@example.com", is_verified=False, is_superuser=True)
    send_email_on_user_create(sender=CustomUser, instance=user, created=True)

    mock_queue.enqueue.assert_not_called()
