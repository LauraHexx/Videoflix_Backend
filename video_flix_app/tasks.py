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
from video_flix_app.models import Video, VideoResolution


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


@job('default')
def transcode_video(video_s3_key, target_height, video_id=None):
    """Transcode video from S3/MinIO and upload result back."""
    base_name, ext = os.path.splitext(os.path.basename(video_s3_key))

    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_input:
        temp_input_path = temp_input.name

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_output:
        temp_output_path = temp_output.name

    try:
        # Download original video from S3/MinIO
        if not download_from_s3(video_s3_key, temp_input_path):
            raise Exception(
                f"Failed to download video from S3: {video_s3_key}")

        # Transcode video
        subprocess.run([
            'ffmpeg', '-i', temp_input_path,
            '-vf', f"scale=-2:{target_height}",
            '-c:a', 'copy',
            '-y',  # Overwrite output file
            temp_output_path
        ], check=True)

        # Upload transcoded video to S3/MinIO
        output_filename = f"{base_name}_{target_height}p{ext}"
        output_s3_key = f"videos/{target_height}p/{output_filename}"

        if not upload_to_s3(temp_output_path, output_s3_key):
            raise Exception(
                f"Failed to upload transcoded video to S3: {output_s3_key}")

        # Save video resolution to database
        if video_id:
            VideoResolution.objects.create(
                video_id=video_id,
                height=target_height,
                file=output_s3_key
            )

        return output_s3_key

    finally:
        # Clean up temporary files
        for temp_file in [temp_input_path, temp_output_path]:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


@job('default')
def process_video_pipeline(video_s3_key, video_id=None):
    """Process video pipeline: generate thumbnail and queue transcoding jobs."""

    set_video_duration(video_s3_key, video_id)

    # Generate thumbnail
    thumbnail_s3_key = generate_thumbnail(video_s3_key)

    # Update video model with thumbnail
    if video_id:
        Video.objects.filter(id=video_id).update(thumbnail=thumbnail_s3_key)

    # Queue transcoding jobs
    target_heights = [120, 360, 720, 1080]
    queue = django_rq.get_queue('default')

    for height in target_heights:
        queue.enqueue(transcode_video, video_s3_key, height, video_id)

    return {
        'thumbnail': thumbnail_s3_key,
        'queued_resolutions': target_heights
    }
