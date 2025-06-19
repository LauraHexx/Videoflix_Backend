import pytest
import uuid
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from users_auth_app.models import CustomUser
from users_auth_app.api.serializers import RegistrationSerializer
from utils.test_utils import create_verified_user, create_unverified_user
from rest_framework.authtoken.models import Token

REGISTER_URL = "/api/registration/"
VERIFY_URL = "/api/registration/verify/"


@pytest.fixture
def api_client():
    """Returns a DRF APIClient instance."""
    return APIClient()


@pytest.mark.django_db
def test_registration_success(api_client):
    """Registering a new user returns 201 and token."""
    data = {"email": "newuser@example.com",
            "password": "pw123456", "repeated_password": "pw123456"}
    response = api_client.post(REGISTER_URL, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert "token" in response.data
    assert CustomUser.objects.filter(email="newuser@example.com").exists()


@pytest.mark.django_db
def test_registration_existing_verified_user_fails(api_client):
    """Registering with an existing verified email returns 400."""
    user, _ = create_verified_user(email="exists@example.com")
    data = {"email": user.email, "password": "pw123456",
            "repeated_password": "pw123456"}
    response = api_client.post(REGISTER_URL, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


@pytest.mark.django_db
def test_registration_existing_unverified_user_updates(api_client):
    """Registering with an existing unverified email updates password and returns 200."""
    user, _ = create_unverified_user(email="unverified@example.com")
    data = {"email": user.email, "password": "pw123456",
            "repeated_password": "pw123456"}
    response = api_client.post(REGISTER_URL, data)
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.check_password("pw123456")


@pytest.mark.django_db
def test_registration_passwords_do_not_match(api_client):
    """Registration fails if passwords do not match."""
    data = {"email": "fail@example.com",
            "password": "pw123456", "repeated_password": "pw654321"}
    response = api_client.post(REGISTER_URL, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "non_field_errors" in response.data or "Passwords do not match." in str(
        response.data)


@pytest.mark.django_db
def test_registration_missing_fields(api_client):
    """Registration fails if required fields are missing."""
    response = api_client.post(REGISTER_URL, {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_registration_invalid_email(api_client):
    """Registration fails with invalid email format."""
    data = {"email": "not-an-email", "password": "pw123456",
            "repeated_password": "pw123456"}
    response = api_client.post(REGISTER_URL, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_registration_returns_token_and_user_data(api_client):
    """Registration returns token, email, and user_id."""
    data = {"email": "tokentest@example.com",
            "password": "pw123456", "repeated_password": "pw123456"}
    response = api_client.post(REGISTER_URL, data)
    assert "token" in response.data
    assert "email" in response.data
    assert "user_id" in response.data


@pytest.mark.django_db
def test_registration_serializer_create_new_user():
    """RegistrationSerializer creates a new user."""
    data = {"email": "serializer@example.com",
            "password": "pw123456", "repeated_password": "pw123456"}
    serializer = RegistrationSerializer(data=data)
    assert serializer.is_valid()
    user, created = serializer.save()
    assert created
    assert user.email == "serializer@example.com"


@pytest.mark.django_db
def test_registration_serializer_update_unverified_user():
    """RegistrationSerializer updates an unverified user."""
    user, _ = create_unverified_user(email="update@example.com")
    data = {"email": user.email, "password": "pw123456",
            "repeated_password": "pw123456"}
    serializer = RegistrationSerializer(data=data)
    assert serializer.is_valid()
    updated_user, created = serializer.save()
    assert not created
    assert updated_user.check_password("pw123456")


@pytest.mark.django_db
def test_registration_verify_view_success(api_client):
    """RegistrationVerifyView verifies user with valid token."""
    user, _ = create_unverified_user(email="verifyme@example.com")
    token = str(uuid.uuid4())
    user.verification_token = token
    user.save()
    url = f"{VERIFY_URL}{token}/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.is_verified
    assert user.verification_token is None


@pytest.mark.django_db
def test_registration_verify_view_invalid_token(api_client):
    """RegistrationVerifyView fails with invalid token."""
    token = str(uuid.uuid4())
    url = f"{VERIFY_URL}{token}/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_registration_verify_view_missing_token(api_client):
    """RegistrationVerifyView fails with missing token."""
    url = f"{VERIFY_URL}/"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
