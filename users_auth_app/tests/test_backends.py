
from utils.test_utils import create_verified_user, create_unverified_user
from users_auth_app.api.backends import VerifiedEmailBackend, UnsafeTLSBackend
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


@pytest.fixture
def backend():
    """Return an instance of UnsafeTLSBackend."""
    return UnsafeTLSBackend()


def test_open_returns_false_if_connection_exists(backend):
    """open returns False if connection already exists."""
    backend.connection = object()
    assert backend.open() is False


def test_open_success(monkeypatch):
    """open returns True if connection, TLS and login succeed."""
    backend = UnsafeTLSBackend()
    monkeypatch.setattr(backend, "_create_smtp_connection", lambda: "conn")
    monkeypatch.setattr(backend, "_start_tls_if_needed", lambda: None)
    monkeypatch.setattr(backend, "_login_if_needed", lambda: None)
    backend.connection = None
    assert backend.open() is True
    assert backend.connection == "conn"


def test_open_fail_silently(monkeypatch):
    """open returns False if exception and fail_silently is True."""
    backend = UnsafeTLSBackend(fail_silently=True)
    monkeypatch.setattr(backend, "_create_smtp_connection", lambda: 1/0)
    assert backend.open() is False


def test_open_raises(monkeypatch):
    """open raises exception if fail_silently is False."""
    backend = UnsafeTLSBackend(fail_silently=False)
    monkeypatch.setattr(backend, "_create_smtp_connection", lambda: 1/0)
    with pytest.raises(ZeroDivisionError):
        backend.open()


def test_create_smtp_connection(monkeypatch):
    """_create_smtp_connection returns SMTP instance."""
    class DummySMTP:
        def __init__(self, host, port, timeout): self.args = (
            host, port, timeout)
    monkeypatch.setattr("smtplib.SMTP", DummySMTP)
    backend = UnsafeTLSBackend()
    backend.host = "h"
    backend.port = 123
    backend.timeout = 5
    smtp = backend._create_smtp_connection()
    assert isinstance(smtp, DummySMTP)
    assert smtp.args == ("h", 123, 5)


def test_start_tls_if_needed_runs(monkeypatch):
    """_start_tls_if_needed runs starttls with unverified context if use_tls."""
    backend = UnsafeTLSBackend()
    backend.use_tls = True
    backend.connection = type(
        "C", (), {"starttls": lambda self, context: setattr(backend, "tls", context)})()
    monkeypatch.setattr("ssl._create_unverified_context", lambda: "ctx")
    backend._start_tls_if_needed()
    assert getattr(backend, "tls", None) == "ctx"


def test_start_tls_if_needed_skips_if_no_tls():
    """_start_tls_if_needed does nothing if use_tls is False."""
    backend = UnsafeTLSBackend()
    backend.use_tls = False
    backend.connection = object()
    backend._start_tls_if_needed()  # Should not raise


def test_login_if_needed_calls_login(monkeypatch):
    """_login_if_needed calls login if username and password set."""
    backend = UnsafeTLSBackend()
    backend.username = "u"
    backend.password = "p"
    called = {}

    class Conn:
        def login(self, u, p): called["ok"] = (u, p)
    backend.connection = Conn()
    backend._login_if_needed()
    assert called["ok"] == ("u", "p")


def test_login_if_needed_skips_if_no_credentials():
    """_login_if_needed does nothing if username or password missing."""
    backend = UnsafeTLSBackend()
    backend.username = None
    backend.password = None
    backend.connection = object()
    backend._login_if_needed()  # Should not raise
