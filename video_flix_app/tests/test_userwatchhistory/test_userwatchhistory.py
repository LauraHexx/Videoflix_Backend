import pytest
import unittest.mock as mock
from datetime import datetime, timedelta, timezone
from rest_framework import status
from rest_framework.test import APIClient
from video_flix_app.models import UserWatchHistory, Video
from utils.test_utils import create_regular_user, create_superuser
from video_flix_app.api.signals import export_userwatchhistory_hourly

WATCH_HISTORY_URL = "/api/userwatchhistory/"


@pytest.fixture
def api_client():
    """Returns a DRF APIClient instance."""
    return APIClient()


@pytest.fixture
def user():
    """Creates and returns a regular user."""
    return create_regular_user()


@pytest.fixture
def auth_client(api_client, user):
    """Authenticates the client with a regular user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def video():
    """Creates and returns a video instance."""
    return Video.objects.create(title="Test Video", duration=100)


@pytest.mark.django_db
def test_create_watch_history(auth_client, user, video):
    """Creating a watch history returns 201 and saves correct data."""
    data = {"video": video.id, "progress": 50}
    response = auth_client.post(WATCH_HISTORY_URL, data)
    assert response.status_code == status.HTTP_201_CREATED
    assert UserWatchHistory.objects.filter(user=user, video=video).exists()


@pytest.mark.django_db
def test_create_watch_history_duplicate(auth_client, video):
    """Creating a duplicate watch history returns 400."""
    user = auth_client.handler._force_user
    UserWatchHistory.objects.create(user=user, video=video, progress=20)
    data = {"video": video.id, "progress": 30}
    response = auth_client.post(WATCH_HISTORY_URL, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_watch_history_progress_too_high(auth_client, video):
    """Progress cannot exceed video duration."""
    data = {"video": video.id, "progress": 9999}
    response = auth_client.post(WATCH_HISTORY_URL, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Progress cannot exceed video duration." in str(response.data)


@pytest.mark.django_db
def test_get_own_watch_history(auth_client, user, video):
    """Users can retrieve only their own watch history."""
    history = UserWatchHistory.objects.create(
        user=user, video=video, progress=10)
    response = auth_client.get(WATCH_HISTORY_URL)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["progress"] == 10


@pytest.mark.django_db
def test_watch_history_update(auth_client, user, video):
    """User can update progress of their watch history."""
    history = UserWatchHistory.objects.create(
        user=user, video=video, progress=10)
    url = f"{WATCH_HISTORY_URL}{history.id}/"
    response = auth_client.patch(url, {"progress": 80})
    assert response.status_code == status.HTTP_200_OK
    history.refresh_from_db()
    assert history.progress == 80


@pytest.mark.django_db
def test_delete_not_allowed_for_normal_user(auth_client, video):
    """Regular user cannot delete watch history."""
    user = auth_client.handler._force_user
    history = UserWatchHistory.objects.create(
        user=user, video=video, progress=10)
    url = f"{WATCH_HISTORY_URL}{history.id}/"
    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_can_delete_watch_history(api_client, video):
    """Admin can delete any watch history entry."""
    admin = create_superuser()
    api_client.force_authenticate(user=admin)
    user = create_regular_user(email="other@example.com")
    history = UserWatchHistory.objects.create(
        user=user, video=video, progress=10)
    url = f"{WATCH_HISTORY_URL}{history.id}/"
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not UserWatchHistory.objects.filter(id=history.id).exists()


@pytest.mark.django_db
def test_watch_history_filter_by_video(auth_client, user, video):
    """Filtering watch history by video returns correct entry."""
    other_video = Video.objects.create(title="Other", duration=100)
    UserWatchHistory.objects.create(user=user, video=video, progress=10)
    UserWatchHistory.objects.create(user=user, video=other_video, progress=30)
    response = auth_client.get(WATCH_HISTORY_URL + f"?video={video.id}")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["video"] == video.id


def patch_export_and_cache(mocker):
    """
    Patch export_model_to_s3 and cache.set/get for the signal test.
    Returns the export mock and sets up cache.get side effects.
    """
    mock_export = mocker.patch("video_flix_app.api.signals.export_model_to_s3")
    mocker.patch("django.core.cache.cache.set")
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(hours=2)
    cache_get_values = [None, now, old_time]
    mocker.patch(
        "django.core.cache.cache.get",
        side_effect=lambda *a, **kw: cache_get_values.pop(0)
    )
    return mock_export


def create_watchhistory_instance(user, video, progress=10):
    """
    Create a UserWatchHistory instance (not saved).
    """
    return UserWatchHistory(user=user, video=video, progress=progress)


def assert_export_call_count(mock_export, expected):
    """
    Assert the export mock was called expected times.
    """
    assert mock_export.call_count == expected


@pytest.mark.django_db
def test_export_userwatchhistory_hourly_signal(mocker, video):
    """
    Export is triggered only if last export was more than 1 hour ago.
    """
    user = create_regular_user()
    instance = create_watchhistory_instance(user, video)
    mock_export = patch_export_and_cache(mocker)

    export_userwatchhistory_hourly(UserWatchHistory, instance)
    assert_export_call_count(mock_export, 1)

    export_userwatchhistory_hourly(UserWatchHistory, instance)
    assert_export_call_count(mock_export, 1)

    export_userwatchhistory_hourly(UserWatchHistory, instance)
    assert_export_call_count(mock_export, 2)
