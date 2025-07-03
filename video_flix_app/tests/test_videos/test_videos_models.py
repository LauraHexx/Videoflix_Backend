import pytest
from video_flix_app.models import Video, video_file_upload_to


@pytest.mark.django_db
def test_video_str_returns_title():
    """__str__ returns the video title."""
    video = Video(title="Test Video")
    assert str(video) == "Test Video"


def test_video_file_upload_to_format():
    """Upload path contains base, timestamp and random 7-char id."""
    filename = "video.mp4"
    path = video_file_upload_to(None, filename)
    base, ext = path.split("/")[-1].split("_")[0], path.split(".")[-1]
    assert ext == "mp4"
    assert path.startswith("videos/video_")
    assert len(path.split("_")[2].split(".")[0]) == 7


@pytest.mark.django_db
def test_video_str_returns_title():
    """__str__ returns the video title."""
    video = Video(title="Test Video")
    assert str(video) == "Test Video"


def test_video_file_upload_to_format():
    """Upload path contains base, timestamp and random 7-char id."""
    filename = "video.mp4"
    path = video_file_upload_to(None, filename)
    base, ext = path.split("/")[-1].split("_")[0], path.split(".")[-1]
    assert ext == "mp4"
    assert path.startswith("videos/video_")
    assert len(path.split("_")[2].split(".")[0]) == 7


@pytest.mark.django_db
def test_post_delete_signal_enqueues_deletion(mocker):
    """post_delete signal triggers video deletion enqueue."""
    mock_queue = mocker.patch(
        "video_flix_app.api.signals.django_rq.get_queue").return_value
    video = Video.objects.create(
        title="X",
        video_file="file.mp4",
        thumbnail="thumb.jpg",
        hls_playlist="hls/master.m3u8"
    )
    mock_queue.reset_mock()
    video.delete()
    mock_queue.enqueue.assert_called_once()
