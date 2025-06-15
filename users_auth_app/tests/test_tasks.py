import uuid
import pytest
from unittest.mock import patch, MagicMock
from users_auth_app.api.tasks import get_user_by_id, generate_verification_token, build_verification_link, get_email_connection, send_email

from utils.test_utils import create_verified_user


@pytest.mark.django_db
def test_get_user_by_id_existing():
    """Test retrieving an existing user by ID."""
    user, _ = create_verified_user()
    assert get_user_by_id(user.id) == user


@pytest.mark.django_db
def test_get_user_by_id_non_existing():
    """Test retrieving a non-existing user by ID returns None."""
    assert get_user_by_id(99999) is None


def test_generate_verification_token():
    """Test that the generated token is a valid UUID string."""
    token = generate_verification_token()
    assert uuid.UUID(token)
    assert isinstance(token, str)


def test_generate_verification_token_uniqueness():
    """Test that generated tokens are unique."""
    tokens = {generate_verification_token() for _ in range(10)}
    assert len(tokens) == 10


def test_build_verification_link_with_custom_backend_url(settings):
    """Test link generation with a custom BACKEND_URL."""
    settings.BACKEND_URL = "https://example.com"
    token = "xyz789"
    link = build_verification_link(token)
    assert link == f"https://example.com/api/registration/verify/{token}/"


@patch("users_auth_app.api.tasks.get_connection")
def test_get_email_connection_success(mock_get_connection):
    """Test successful retrieval of email connection."""
    mock_conn = MagicMock()
    mock_get_connection.return_value = mock_conn
    result = get_email_connection()
    assert result == mock_conn


@patch("users_auth_app.api.tasks.get_connection", side_effect=Exception("SMTP error"))
def test_get_email_connection_failure(mock_get_connection):
    """Test failure when getting email connection returns None."""
    result = get_email_connection()
    assert result is None


@patch("users_auth_app.api.tasks.EmailMultiAlternatives")
def test_send_email_success(mock_email_class):
    """Test sending email successfully using provided connection."""
    mock_msg = MagicMock()
    mock_email_class.return_value = mock_msg

    send_email("user@example.com", "<h1>Test</h1>", connection=MagicMock())
    mock_msg.send.assert_called_once()


@patch("users_auth_app.api.tasks.EmailMultiAlternatives")
def test_send_email_no_connection(mock_email_class):
    """Test that email is not sent if no connection is provided."""
    send_email("user@example.com", "<h1>Test</h1>", connection=None)
    mock_email_class.assert_not_called()


@patch("users_auth_app.api.tasks.EmailMultiAlternatives")
def test_send_email_error_handling(mock_email_class):
    """Test error handling when sending email fails."""
    mock_msg = MagicMock()
    mock_msg.send.side_effect = Exception("Send failed")
    mock_email_class.return_value = mock_msg

    send_email("user@example.com", "<h1>Test</h1>", connection=MagicMock())
    mock_msg.send.assert_called_once()
