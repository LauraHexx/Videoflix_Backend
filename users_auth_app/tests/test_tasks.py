import pytest
from users_auth_app.api import tasks
from utils.test_utils import create_verified_user, create_unverified_user
import uuid


@pytest.mark.django_db
def test_get_user_by_id_found():
    """get_user_by_id returns user if found."""
    user, _ = create_verified_user()
    found = tasks.get_user_by_id(user.id)
    assert found == user


@pytest.mark.django_db
def test_get_user_by_id_not_found():
    """get_user_by_id returns None if user not found."""
    assert tasks.get_user_by_id(999999) is None


def test_generate_verification_token_returns_uuid():
    """generate_verification_token returns a valid UUID string."""
    token = tasks.generate_verification_token()
    assert isinstance(uuid.UUID(token), uuid.UUID)


@pytest.mark.django_db
def test_save_verification_token_sets_token():
    """save_verification_token sets the user's verification_token."""
    user, _ = create_unverified_user()
    token = str(uuid.uuid4())
    tasks.save_verification_token(user, token)
    user.refresh_from_db()
    assert str(user.verification_token) == token


def test_build_verification_link_uses_backend_url(settings):
    """build_verification_link uses BACKEND_URL setting."""
    settings.BACKEND_URL = "http://testserver"
    token = "abc"
    link = tasks.build_verification_link(token)
    assert link == "http://testserver/api/registration/verify/abc/"


def test_render_email_html_renders_string():
    """render_email_html returns a string with verification link."""
    class DummyUser:
        pass
    user = DummyUser()
    html = tasks.render_email_html(user, "http://link")
    assert isinstance(html, str)


def test_get_email_connection_success(monkeypatch, settings):
    """get_email_connection returns a connection if settings are valid."""
    settings.EMAIL_HOST = "smtp.example.com"
    settings.EMAIL_PORT = 587
    settings.EMAIL_HOST_USER = "user"
    settings.EMAIL_HOST_PASSWORD = "pass"
    settings.EMAIL_USE_TLS = True
    settings.EMAIL_USE_SSL = False
    monkeypatch.setattr("django.core.mail.get_connection",
                        lambda **kwargs: object())
    conn = tasks.get_email_connection()
    assert conn is not None


def test_get_email_connection_failure(monkeypatch):
    """get_email_connection returns None if connection fails."""
    def raise_exc(*args, **kwargs): raise Exception("fail")
    monkeypatch.setattr("users_auth_app.api.tasks.get_connection", raise_exc)
    assert tasks.get_email_connection() is None


def test_send_email_success(monkeypatch):
    """send_email calls send on the message object."""
    class DummyMsg:
        def attach_alternative(self, html, mime): pass
        def send(self): pass

    class DummyConn:
        def send_messages(self, messages):
            for msg in messages:
                msg.send()
            return 1

    monkeypatch.setattr(
        "django.core.mail.EmailMultiAlternatives", lambda *a, **k: DummyMsg())
    tasks.send_email("a@b.com", "<html></html>", DummyConn(), "subject")


def test_send_email_no_connection():
    """send_email does nothing if connection is None."""
    tasks.send_email("a@b.com", "<html></html>", None,
                     "subject")


@pytest.mark.django_db
def test_send_verification_email_task_full(monkeypatch):
    """send_verification_email_task runs all steps for a valid user."""
    user, _ = create_unverified_user()
    monkeypatch.setattr(tasks, "generate_verification_token",
                        lambda: str(uuid.uuid4()))
    monkeypatch.setattr(tasks, "render_email_html",
                        lambda u, l: "<html></html>")
    monkeypatch.setattr(tasks, "get_email_connection", lambda: object())
    monkeypatch.setattr(tasks, "send_email", lambda *a, **k: None)
    tasks.send_verification_email_task(user.id)
    user.refresh_from_db()
    assert user.verification_token is not None


@pytest.mark.django_db
def test_send_verification_email_task_user_not_found():
    """send_verification_email_task does nothing if user not found."""
    tasks.send_verification_email_task(999999)  # Should not raise


def test_build_password_reset_link_uses_frontend_url(settings):
    """build_password_reset_link uses FRONTEND_URL setting."""
    settings.FRONTEND_URL = "http://frontend"
    token = "abc"
    link = tasks.build_password_reset_link(token)
    assert link == "http://frontend/reset-password/abc/"


def test_render_password_reset_email_html_returns_string():
    """render_password_reset_email_html returns a string."""
    html = tasks.render_password_reset_email_html("http://reset")
    assert isinstance(html, str)


@pytest.mark.django_db
def test_send_password_reset_email_task_full(monkeypatch):
    """send_password_reset_email_task runs all steps for a valid user."""
    user, _ = create_verified_user()
    user.verification_token = uuid.uuid4()
    user.save()
    monkeypatch.setattr(
        tasks, "render_password_reset_email_html", lambda l: "<html></html>")
    monkeypatch.setattr(tasks, "get_email_connection", lambda: object())
    monkeypatch.setattr(tasks, "send_email", lambda *a, **k: None)
    tasks.send_password_reset_email_task(user.id)
