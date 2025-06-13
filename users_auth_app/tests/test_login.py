import pytest
from rest_framework import status
from utils.test_utils import create_verified_user, create_unverified_user
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return DRF APIClient instance for request simulation."""
    return APIClient()


def login(api_client, email, password):
    """Perform login POST request with email and password."""
    url = "/login/"
    return api_client.post(url, {"email": email, "password": password})


@pytest.mark.django_db
def test_login_success(api_client):
    """Test login with valid credentials and verified user returns token and 200."""
    user, password = create_verified_user()
    response = login(api_client, user.email, password)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "token" in data
    assert data["email"] == user.email
    assert "user_id" in data


@pytest.mark.django_db
def test_login_unverified_user_fails(api_client):
    """Test login fails with 400 for unverified user, generic error returned."""
    user, password = create_unverified_user()
    response = login(api_client, user.email, password)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "Invalid login credentials."


@pytest.mark.django_db
def test_login_wrong_password_fails(api_client):
    """Test login fails with 400 for wrong password, generic error returned."""
    user, _ = create_verified_user()
    wrong_password = "wrongpass"
    response = login(api_client, user.email, wrong_password)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "Invalid login credentials."


@pytest.mark.django_db
def test_login_invalid_email_format_fails(api_client):
    """Test login fails with 400 for invalid email format."""
    response = login(api_client, "not-an-email", "anyPassword")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_data = response.json()
    assert "error" in json_data or "email" in json_data


@pytest.mark.django_db
def test_login_missing_password_fails(api_client):
    """Test login fails with 400 when password is missing."""
    response = api_client.post("/login/", {"email": "user@example.com"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_login_missing_email_fails(api_client):
    """Test login fails with 400 when email is missing."""
    response = api_client.post("/login/", {"password": "testpass123"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
