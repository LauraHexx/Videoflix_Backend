import os
import subprocess
import tempfile
import django_rq
import boto3
import tempfile
from moviepy.editor import VideoFileClip

from botocore.exceptions import NoCredentialsError, ClientError
from django.conf import settings
from django_rq import job
from video_flix_app.models import Video
from video_flix_app.api.serializers import generate_presigned_url


def get_s3_client():
    """Get configured S3/MinIO client."""
    return boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        use_ssl=settings.AWS_S3_USE_SSL,
        verify=settings.AWS_S3_VERIFY
    )


def download_from_s3(s3_key, local_path):
    """Download file from S3/MinIO to local path."""
    try:
        s3_client = get_s3_client()
        s3_client.download_file(
            settings.AWS_STORAGE_BUCKET_NAME, s3_key, local_path)
        return True
    except (NoCredentialsError, ClientError) as e:
        print(f"Error downloading from S3: {e}")
        return False


def upload_to_s3(local_path, s3_key):
    """Upload file from local path to S3/MinIO."""
    try:
        s3_client = get_s3_client()
        s3_client.upload_file(
            local_path, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
        return True
    except (NoCredentialsError, ClientError) as e:
        print(f"Error uploading to S3: {e}")
        return False


def get_temp_file(suffix):
    """Create a temporary file and return its path."""
    return tempfile.NamedTemporaryFile(suffix=suffix, delete=False).name


def cleanup_files(paths):
    """Delete files if they exist."""
    for path in paths:
        if os.path.exists(path):
            os.unlink(path)


def get_video_duration(path):
    """Return video duration in seconds."""
    clip = VideoFileClip(path)
    return int(clip.duration)


def update_video_duration(video_id, duration):
    """Update duration field in Video model."""
    Video.objects.filter(id=video_id).update(duration=duration)


def set_video_duration(video_s3_key, video_id=None):
    """Download video, get duration, and update Video model."""
    temp_path = get_temp_file('.mp4')
    try:
        if not download_from_s3(video_s3_key, temp_path):
            return None
        if video_id:
            duration = get_video_duration(temp_path)
            update_video_duration(video_id, duration)
            return duration
    except Exception:
        return None
    finally:
        cleanup_files([temp_path])


@job('default')
def generate_thumbnail(video_s3_key):
    """Generate thumbnail from video stored in S3/MinIO."""
    base_name = os.path.splitext(os.path.basename(video_s3_key))[0]

    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
        temp_video_path = temp_video.name

    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_thumb:
        temp_thumb_path = temp_thumb.name

    try:
        # Download video from S3/MinIO
        if not download_from_s3(video_s3_key, temp_video_path):
            raise Exception(
                f"Failed to download video from S3: {video_s3_key}")

        # Generate thumbnail
        subprocess.run([
            'ffmpeg', '-i', temp_video_path,
            '-ss', '00:00:01',
            '-vframes', '1',
            '-y',  # Overwrite output file
            temp_thumb_path
        ], check=True)

        # Upload thumbnail to S3/MinIO
        thumb_s3_key = f"thumbnails/{base_name}.jpg"
        if not upload_to_s3(temp_thumb_path, thumb_s3_key):
            raise Exception(
                f"Failed to upload thumbnail to S3: {thumb_s3_key}")

        return thumb_s3_key

    finally:
        # Clean up temporary files
        for temp_file in [temp_video_path, temp_thumb_path]:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


def transcode_to_hls(input_path, output_dir, base_name, height):
    """
    Transcode video to HLS format (.m3u8 + .ts segments) for a specific height.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{base_name}_{height}p.m3u8")

    bitrate_map = {
        120:  100,
        360:  600,     # SD
        720:  1800,    # HD ready
        1080: 3500     # Full HD
    }

    maxrate_map = {
        120:  150,     # ca. 1.5x bitrate
        360:  900,     # ca. 1.5x bitrate
        720:  2500,    # ca. 1.4x bitrate
        1080: 5000     # ca. 1.4x bitrate
    }

    bufsize_map = {
        120:  300,     # ca. 2x maxrate
        360:  1800,
        720:  5000,
        1080: 10000
    }

    bitrate = bitrate_map.get(height, 1000)
    maxrate = maxrate_map.get(height, 1200)
    bufsize = bufsize_map.get(height, 2000)

    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-vf", f"scale=-2:{height}",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", "128k",
        "-c:v", "h264",
        "-profile:v", "main",
        "-crf", "20",
        "-sc_threshold", "0",
        "-g", "48",
        "-keyint_min", "48",
        "-hls_time", "10",
        "-hls_playlist_type", "vod",
        "-b:v", f"{bitrate}k",
        "-maxrate", f"{maxrate}k",
        "-bufsize", f"{bufsize}k",
        "-hls_segment_filename", os.path.join(output_dir,
                                              f"{base_name}_{height}p_%03d.ts"),
        output_path
    ], check=True)
    return output_path


def create_master_playlist(output_dir, base_name, heights):
    """
    Create a master HLS playlist referencing all variant playlists.
    """
    master_path = os.path.join(output_dir, f"{base_name}_master.m3u8")
    with open(master_path, "w") as f:
        f.write("#EXTM3U\n")
        for h in heights:
            f.write(
                f'#EXT-X-STREAM-INF:BANDWIDTH={h*1000*2},RESOLUTION=1920x{h}\n')
            f.write(f"{base_name}_{h}p.m3u8\n")
    return master_path


def sign_ts_segment_urls(playlist_path, base_name):
    """
    Replace all .ts segment paths in a playlist with signed S3 URLs.
    """

    with open(playlist_path, "r") as f:
        lines = f.readlines()

    signed_lines = []
    for line in lines:
        if line.strip().endswith(".ts"):
            s3_key = f"hls/{base_name}/{line.strip()}"
            signed_url = generate_presigned_url(s3_key)
            signed_lines.append(signed_url + "\n")
        else:
            signed_lines.append(line)

    with open(playlist_path, "w") as f:
        f.writelines(signed_lines)


def create_signed_master_playlist(output_dir, base_name, heights):
    """
    Create a master HLS playlist with signed URLs for each resolution playlist.
    """

    master_path = os.path.join(output_dir, f"{base_name}_master.m3u8")
    with open(master_path, "w") as f:
        f.write("#EXTM3U\n")
        for h in heights:
            s3_key = f"hls/{base_name}/{base_name}_{h}p.m3u8"
            signed_url = generate_presigned_url(s3_key)
            f.write(
                f'#EXT-X-STREAM-INF:BANDWIDTH={h*1000*2},RESOLUTION=1920x{h}\n')
            f.write(f"{signed_url}\n")
    return master_path


@job('default')
def transcode_video_to_hls(video_s3_key, video_id=None):
    """
    Transcode video to HLS (120p, 360p, 720p, 1080p), inject signed URLs, and upload to S3.
    """
    base_name, ext = os.path.splitext(os.path.basename(video_s3_key))
    heights = [120, 360, 720, 1080]
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_input:
        temp_input_path = temp_input.name
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            if not download_from_s3(video_s3_key, temp_input_path):
                raise Exception(
                    f"Failed to download video from S3: {video_s3_key}")
            for h in heights:
                transcode_to_hls(temp_input_path, temp_dir, base_name, h)
            for h in heights:
                sub_path = os.path.join(temp_dir, f"{base_name}_{h}p.m3u8")
                sign_ts_segment_urls(sub_path, base_name)
            master_path = create_signed_master_playlist(
                temp_dir, base_name, heights)
            for fname in os.listdir(temp_dir):
                fpath = os.path.join(temp_dir, fname)
                s3_key = f"hls/{base_name}/{fname}"
                upload_to_s3(fpath, s3_key)
            if video_id:
                Video.objects.filter(id=video_id).update(
                    hls_playlist=f"hls/{base_name}/{base_name}_master.m3u8"
                )
            return f"hls/{base_name}/{base_name}_master.m3u8"
        finally:
            cleanup_files([temp_input_path])


@job('default')
def process_video_pipeline(video_s3_key, video_id=None):
    """Process video pipeline: generate thumbnail and queue HLS transcoding job."""
    set_video_duration(video_s3_key, video_id)
    thumbnail_s3_key = generate_thumbnail(video_s3_key)
    if video_id:
        Video.objects.filter(id=video_id).update(thumbnail=thumbnail_s3_key)
    queue = django_rq.get_queue('default')
    queue.enqueue(transcode_video_to_hls, video_s3_key, video_id)
    return {
        'thumbnail': thumbnail_s3_key,
        'queued': 'hls'
    }
