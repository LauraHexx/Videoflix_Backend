import pytest
from video_flix_app.api.tasks import (
    process_video_pipeline,
    generate_thumbnail_and_save,
    transcode_video_to_hls,
    delete_video_assets_from_s3,
)
from video_flix_app.models import Video
from unittest.mock import patch
from io import StringIO, BytesIO


@pytest.mark.django_db
def test_generate_thumbnail_and_save_updates_db(mocker):
    """generate_thumbnail_and_save updates video thumbnail field."""
    video = Video.objects.create(title="ThumbVid")
    mocker.patch("video_flix_app.api.tasks.generate_thumbnail",
                 return_value="thumb_key")
    generate_thumbnail_and_save(video.video_file.name, video.id, "base_name")
    video.refresh_from_db()
    assert video.thumbnail == "thumb_key"


# @patch("subprocess.run")
# def test_transcode_video_to_hls_runs_ffmpeg(mock_subprocess, mocker, tmp_path):
#    """transcode_video_to_hls runs without error."""
#    mocker.patch("video_flix_app.api.tasks.download_from_s3",
#                 return_value=True)
#    mocker.patch("video_flix_app.api.tasks.upload_hls_to_s3")
#    mocker.patch("video_flix_app.api.tasks.update_video_hls_field")
#
#    def open_mock(file, mode='r', *args, **kwargs):
#        # Für .json-Dateien IMMER gültiges JSON liefern
#        if file.endswith('.json'):
#            if 'b' in mode:
#                return BytesIO(b'{}')
#            return StringIO('{}')
#        if 'b' in mode:
#            return BytesIO()
#        return StringIO()
#    mocker.patch("builtins.open", open_mock)
#
#    from video_flix_app.api.tasks import transcode_video_to_hls
#    result = transcode_video_to_hls("input.mp4", str(tmp_path), "base_name")
#    assert result.endswith(".m3u8")


@pytest.mark.django_db
def test_delete_video_assets_from_s3_calls_deletes(mocker):
    """delete_video_assets_from_s3 deletes video assets on S3."""
    mock_s3_client = mocker.Mock()
    mocker.patch("video_flix_app.api.tasks.get_s3_client",
                 return_value=mock_s3_client)
    delete_video_assets_from_s3("hls_key", "thumb_key", "video_key")
    assert mock_s3_client.delete_object.called


def get_encoding_params(height):
    """Return bitrate, maxrate and bufsize for the given video height."""
    bitrate_map = {120: 100, 360: 600, 720: 1800, 1080: 3500}
    maxrate_map = {120: 150, 360: 900, 720: 2500, 1080: 5000}
    bufsize_map = {120: 300, 360: 1800, 720: 5000, 1080: 10000}
    bitrate = bitrate_map.get(height, 1000)
    maxrate = maxrate_map.get(height, 1200)
    bufsize = bufsize_map.get(height, 2000)
    return bitrate, maxrate, bufsize


def test_get_encoding_params_returns_expected_values():
    """Returns bitrate, maxrate, bufsize for known heights."""
    bitrate, maxrate, bufsize = get_encoding_params(360)
    assert bitrate == 600
    assert maxrate == 900
    assert bufsize == 1800


def test_get_encoding_params_default_values():
    """Returns default encoding params for unknown height."""
    bitrate, maxrate, bufsize = get_encoding_params(999)
    assert bitrate == 1000
    assert maxrate == 1200
    assert bufsize == 2000
