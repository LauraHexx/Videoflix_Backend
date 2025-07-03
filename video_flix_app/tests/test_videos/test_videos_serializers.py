import pytest
from video_flix_app.api.serializers import VideoSerializer
from video_flix_app.models import Video
from unittest.mock import patch


@pytest.mark.django_db
def test_video_serializer_fields(mocker):
    """VideoSerializer serializes expected fields."""
    mocker.patch("django_rq.get_queue")  # Verhindert Redis-Zugriff

    video = Video.objects.create(title="Test", video_file="file.mp4")
    data = VideoSerializer(video).data

    expected_keys = {"id", "title", "description", "duration", "video_file",
                     "thumbnail", "hls_playlist", "created_at", "updated_at", "genre"}
    assert set(data.keys()) >= expected_keys


@pytest.mark.django_db
def test_thumbnail_and_hls_url_calls_presigned_url(mocker):
    """Thumbnail and HLS URL fields call generate_presigned_url."""
    video = Video.objects.create(
        title="T", thumbnail="thumb", hls_playlist="playlist"
    )
    mocker.patch("video_flix_app.api.serializers.generate_presigned_url",
                 return_value="signed_url")
    serializer = VideoSerializer(video)
    data = serializer.data
    assert data["thumbnail_url"] == "signed_url"
    assert data["hls_playlist_url"] == "signed_url"
