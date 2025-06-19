import pytest
from rest_framework import status
from rest_framework.test import APIClient
from utils.test_utils import create_verified_user, create_unverified_user
import uuid

PASSWORD_RESET_REQUEST_URL = "/api/password-reset/request/"
PASSWORD_RESET_CONFIRM_URL = "/api/password-reset/confirm/"


@pytest.fixture
def api_client():
    """Returns a DRF APIClient instance."""
    return APIClient()


@pytest.mark.django_db
def test_password_reset_request_success(api_client):
    """Password reset request for a verified user returns 200 and sets a token."""
    user, _ = create_verified_user()
    user.verification_token = None
    user.save()
    response = api_client.post(
        PASSWORD_RESET_REQUEST_URL, {"email": user.email})
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.verification_token is not None


@pytest.mark.django_db
def test_password_reset_request_unverified_user(api_client):
    """Password reset request for an unverified user returns 200 but does not set a token."""
    user, _ = create_unverified_user()
    user.verification_token = None
    user.save()
    response = api_client.post(
        PASSWORD_RESET_REQUEST_URL, {"email": user.email})
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.verification_token is None


@pytest.mark.django_db
def test_password_reset_request_unknown_email(api_client):
    """Password reset request for unknown email returns 200."""
    response = api_client.post(PASSWORD_RESET_REQUEST_URL, {
                               "email": "notfound@example.com"})
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_password_reset_request_invalid_email(api_client):
    """Password reset request with invalid email returns 400."""
    response = api_client.post(PASSWORD_RESET_REQUEST_URL, {
                               "email": "not-an-email"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_password_reset_request_missing_email(api_client):
    """Password reset request with missing email returns 400."""
    response = api_client.post(PASSWORD_RESET_REQUEST_URL, {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_password_reset_confirm_success(api_client):
    """Password reset confirm with valid token and matching passwords returns 200 and resets password."""
    user, password = create_verified_user()
    token = uuid.uuid4()
    user.verification_token = token
    user.save()
    new_password = "newsecurepass123"
    response = api_client.post(PASSWORD_RESET_CONFIRM_URL, {
        "token": str(token),
        "password": new_password,
        "password_confirmed": new_password,
    })
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.verification_token is None
    assert user.check_password(new_password)


@pytest.mark.django_db
def test_password_reset_confirm_invalid_token(api_client):
    """Password reset confirm with invalid token returns 400."""
    new_password = "newsecurepass123"
    response = api_client.post(PASSWORD_RESET_CONFIRM_URL, {
        "token": str(uuid.uuid4()),
        "password": new_password,
        "password_confirmed": new_password,
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


@pytest.mark.django_db
def test_password_reset_confirm_passwords_do_not_match(api_client):
    """Password reset confirm with non-matching passwords returns 400."""
    user, password = create_verified_user()
    token = uuid.uuid4()
    user.verification_token = token
    user.save()
    response = api_client.post(PASSWORD_RESET_CONFIRM_URL, {
        "token": str(token),
        "password": "abc123",
        "password_confirmed": "def456",
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Passwords do not match" in str(response.content)


@pytest.mark.django_db
def test_password_reset_confirm_missing_fields(api_client):
    """Password reset confirm with missing fields returns 400."""
    response = api_client.post(PASSWORD_RESET_CONFIRM_URL, {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
