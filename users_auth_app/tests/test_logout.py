import pytest
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from utils.test_utils import create_verified_user

LOGOUT_URL = "/api/logout/"


@pytest.fixture
def api_client():
    """Returns a DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def authenticated_client():
    """Returns a DRF APIClient with valid token header and user."""
    user, password = create_verified_user(email="logout@example.com")
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client, user, token


@pytest.mark.django_db
def test_logout_success(authenticated_client):
    """Logout deletes the user's token and returns 200."""
    client, user, token = authenticated_client
    # Ensure token exists before logout
    assert Token.objects.filter(user=user).exists()
    response = client.post(LOGOUT_URL)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["detail"] == "Successfully logged out."
    assert not Token.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_logout_unauthenticated(api_client):
    """POST without token returns 401."""
    response = api_client.post(LOGOUT_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Authentication credentials were not provided." in str(
        response.data)
