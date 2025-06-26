import pytest
from rest_framework import status
from rest_framework.test import APIClient
from video_flix_app.models import Video
from utils.test_utils import create_regular_user, create_superuser
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import MagicMock, patch

VIDEO_URL = "/api/video/"


@pytest.fixture
def api_client():
    """Return DRF APIClient."""
    return APIClient()


@pytest.fixture
def user():
    """Return regular user."""
    return create_regular_user()


@pytest.fixture
def auth_client(api_client, user):
    """Authenticate client with regular user."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture(autouse=True)
def mock_django_rq_get_queue(mocker):
    """Mock django_rq.get_queue to avoid real Redis connections."""
    mock_queue = mocker.Mock()
    mocker.patch("django_rq.get_queue", return_value=mock_queue)
    return mock_queue


@pytest.fixture(autouse=True)
def mock_boto3_client():
    """Mock boto3 client to prevent real S3 calls."""
    with patch("video_flix_app.api.videos.get_s3_client") as mock_get_s3_client:
        mock_client = MagicMock()
        mock_client.download_file.return_value = True
        mock_client.upload_file.return_value = True
        mock_client.delete_object.return_value = True
        mock_get_s3_client.return_value = mock_client
        yield mock_get_s3_client


@pytest.mark.django_db
def test_create_video_success(auth_client):
    """Authenticated user can create a video."""
    video_file = SimpleUploadedFile(
        "vid.mp4", b"content", content_type="video/mp4")
    data = {"title": "New Video", "video_file": video_file}
    response = auth_client.post(VIDEO_URL, data, format="multipart")
    assert response.status_code == status.HTTP_201_CREATED
    assert Video.objects.filter(title="New Video").exists()


@pytest.mark.django_db
def test_delete_video_admin_only(api_client):
    """Only admin users can delete videos."""
    admin = create_superuser()
    api_client.force_authenticate(admin)
    video = Video.objects.create(title="To Delete")
    url = f"{VIDEO_URL}{video.id}/"
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_delete_video_denied_for_normal_user(auth_client):
    """Normal user cannot delete videos."""
    video = Video.objects.create(title="Forbidden Delete")
    url = f"{VIDEO_URL}{video.id}/"
    response = auth_client.delete(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_random_video_endpoint(auth_client):
    """Random video endpoint returns 200 and video data."""
    Video.objects.create(title="RandVid")
    response = auth_client.get(f"{VIDEO_URL}random/")
    assert response.status_code == status.HTTP_200_OK
    assert "title" in response.data
