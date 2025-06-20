import pytest
from users_auth_app.models import CustomUser
from users_auth_app.api.signals import send_email_on_user_create
from users_auth_app.api.tasks import send_verification_email_task
from utils.test_utils import create_unverified_user, create_verified_user, create_superuser


@pytest.mark.django_db
def test_signal_no_email_for_verified_user(mocker):
    """Signal does not enqueue email for verified user."""
    user, _ = create_verified_user()
    mock_queue = mocker.patch("django_rq.get_queue")
    send_email_on_user_create(CustomUser, user, True)
    mock_queue.assert_not_called()


@pytest.mark.django_db
def test_signal_no_email_for_superuser(mocker):
    """Signal does not enqueue email for superuser."""
    user = create_superuser()
    mock_queue = mocker.patch("django_rq.get_queue")
    send_email_on_user_create(CustomUser, user, True)
    mock_queue.assert_not_called()


@pytest.mark.django_db
def test_signal_enqueue_on_create_unverified(mocker):
    """Signal enqueues email for new unverified user."""
    user, _ = create_unverified_user()
    mock_queue = mocker.patch("django_rq.get_queue")
    queue = mock_queue.return_value
    send_email_on_user_create(CustomUser, user, True)
    queue.enqueue.assert_called_once_with(
        send_verification_email_task, user.pk)


@pytest.mark.django_db
def test_signal_enqueue_on_password_update(mocker):
    """Signal enqueues email if password updated for unverified user."""
    user, _ = create_unverified_user()
    mock_queue = mocker.patch("django_rq.get_queue")
    queue = mock_queue.return_value
    send_email_on_user_create(CustomUser, user, False,
                              update_fields={"password"})
    queue.enqueue.assert_called_once_with(
        send_verification_email_task, user.pk)


@pytest.mark.django_db
def test_signal_no_enqueue_on_irrelevant_update(mocker):
    """Signal does not enqueue email if update_fields does not include password."""
    user, _ = create_unverified_user()
    mock_queue = mocker.patch("django_rq.get_queue")
    send_email_on_user_create(CustomUser, user, False,
                              update_fields={"last_login"})
    mock_queue.return_value.enqueue.assert_not_called()
