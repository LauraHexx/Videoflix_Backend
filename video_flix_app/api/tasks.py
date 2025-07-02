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
from utils.export_utils import export_model_to_s3
from video_flix_app.models import Video, UserWatchHistory
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


def delete_s3_object(s3_client, key):
    """
    Deletes a single object from S3 using the given key.
    """
    try:
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key
        )
    except Exception as e:
        print(f"Error deleting object {key}: {e}")


def get_temp_file(suffix):
    """Create a temporary file and return its path."""
    return tempfile.NamedTemporaryFile(suffix=suffix, delete=False).name


def cleanup_files(paths):
    """Delete files if they exist."""
    for path in paths:
        if os.path.exists(path):
            os.unlink(path)


# DURATION VIDEO#################################################################


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


# NEW VIDEO#################################################################

@job('default')
def generate_thumbnail(video_s3_key, base_name):
    """Generate thumbnail from video stored in S3/MinIO."""
    temp_video_path = get_temp_file('.mp4')
    temp_thumb_path = get_temp_file('.jpg')
    try:
        download_video_for_thumbnail(video_s3_key, temp_video_path)
        create_thumbnail_with_ffmpeg(temp_video_path, temp_thumb_path)
        thumb_s3_key = upload_thumbnail_and_return_key(
            temp_thumb_path, base_name)
        return thumb_s3_key
    finally:
        cleanup_files([temp_video_path, temp_thumb_path])


def download_video_for_thumbnail(video_s3_key, temp_video_path):
    """Download video from S3 for thumbnail generation."""
    if not download_from_s3(video_s3_key, temp_video_path):
        raise Exception(f"Failed to download video from S3: {video_s3_key}")


def create_thumbnail_with_ffmpeg(temp_video_path, temp_thumb_path):
    """Generate thumbnail using ffmpeg."""
    subprocess.run([
        'ffmpeg', '-i', temp_video_path,
        '-ss', '00:00:01',
        '-vframes', '1',
        '-y',
        temp_thumb_path
    ], check=True)


def upload_thumbnail_and_return_key(temp_thumb_path, base_name):
    """Upload thumbnail to S3 and return its key."""
    thumb_s3_key = f"thumbnails/{base_name}.jpg"
    if not upload_to_s3(temp_thumb_path, thumb_s3_key):
        raise Exception(f"Failed to upload thumbnail to S3: {thumb_s3_key}")
    return thumb_s3_key


def get_output_path(output_dir, base_name, height):
    """Return output path for HLS playlist for the given height."""
    return os.path.join(output_dir, f"{base_name}_{height}p.m3u8")


def get_encoding_params(height):
    """Return bitrate, maxrate and bufsize for the given height."""
    bitrate_map = {120: 100, 360: 600, 720: 1800, 1080: 3500}
    maxrate_map = {120: 150, 360: 900, 720: 2500, 1080: 5000}
    bufsize_map = {120: 300, 360: 1800, 720: 5000, 1080: 10000}
    bitrate = bitrate_map.get(height, 1000)
    maxrate = maxrate_map.get(height, 1200)
    bufsize = bufsize_map.get(height, 2000)
    return bitrate, maxrate, bufsize


def run_ffmpeg_hls(input_path, output_path, output_dir, base_name, height,
                   bitrate, maxrate, bufsize):
    """Run ffmpeg command to generate HLS stream for given resolution."""
    segment_template = os.path.join(
        output_dir, f"{base_name}_{height}p_%03d.ts")
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-vf", f"scale=-2:{height}",
        "-c:a", "aac", "-ar", "48000", "-b:a", "128k",
        "-c:v", "h264", "-profile:v", "main", "-crf", "20",
        "-sc_threshold", "0", "-g", "48", "-keyint_min", "48",
        "-hls_time", "10", "-hls_playlist_type", "vod",
        "-b:v", f"{bitrate}k", "-maxrate", f"{maxrate}k", "-bufsize", f"{bufsize}k",
        "-hls_segment_filename", segment_template,
        output_path
    ], check=True)


def transcode_to_hls(input_path, output_dir, base_name, height):
    """
    Transcode input video to HLS (.m3u8 + .ts) for one resolution height.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = get_output_path(output_dir, base_name, height)
    bitrate, maxrate, bufsize = get_encoding_params(height)
    run_ffmpeg_hls(input_path, output_path, output_dir, base_name, height,
                   bitrate, maxrate, bufsize)
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


def transcode_all_heights(input_path, output_dir, base_name, heights):
    """Transcode video to HLS for all requested heights."""
    for h in heights:
        transcode_to_hls(input_path, output_dir, base_name, h)


def sign_all_variant_playlists(output_dir, base_name, heights):
    """Sign all variant .m3u8 playlists with temporary URLs."""
    for h in heights:
        path = os.path.join(output_dir, f"{base_name}_{h}p.m3u8")
        sign_ts_segment_urls(path, base_name)


def upload_hls_to_s3(directory, base_name):
    """Upload all HLS files in directory to S3."""
    for fname in os.listdir(directory):
        fpath = os.path.join(directory, fname)
        s3_key = f"hls/{base_name}/{fname}"
        upload_to_s3(fpath, s3_key)


def update_video_hls_field(video_id, base_name):
    """Update the hls_playlist field in the Video model."""
    if video_id:
        Video.objects.filter(id=video_id).update(
            hls_playlist=f"hls/{base_name}/{base_name}_master.m3u8"
        )


@job('default')
def transcode_video_to_hls(video_s3_key, video_id, base_name):
    """
    Orchestrates HLS transcoding: download, transcode, sign URLs, upload and update model.
    """
    ext = os.path.splitext(video_s3_key)[1]
    heights = [120, 360, 720, 1080]
    temp_input_path = get_temp_file(ext)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            if not download_from_s3(video_s3_key, temp_input_path):
                raise Exception(f"Failed to download video: {video_s3_key}")
            transcode_all_heights(
                temp_input_path, temp_dir, base_name, heights)
            sign_all_variant_playlists(temp_dir, base_name, heights)
            master_path = create_signed_master_playlist(
                temp_dir, base_name, heights)
            upload_hls_to_s3(temp_dir, base_name)
            update_video_hls_field(video_id, base_name)
            return master_path
        finally:
            cleanup_files([temp_input_path])


@job('default')
def generate_thumbnail_and_save(video_s3_key, video_id, base_name):
    """Wrapper for thumbnail generation with DB update."""
    thumbnail_s3_key = generate_thumbnail(video_s3_key, base_name)
    if video_id:
        Video.objects.filter(id=video_id).update(thumbnail=thumbnail_s3_key)


@job('default')
def process_video_pipeline(video_s3_key, video_id=None):
    """Enqueue both thumbnail generation and HLS transcoding for the given video and exports video."""
    set_video_duration(video_s3_key, video_id)
    base_name = os.path.splitext(os.path.basename(video_s3_key))[0]
    queue = django_rq.get_queue('default')
    queue.enqueue(generate_thumbnail_and_save,
                  video_s3_key, video_id, base_name)
    queue.enqueue(transcode_video_to_hls, video_s3_key, video_id, base_name)
    export_model_to_s3(Video)

    return {"queued": "thumbnail + hls"}

# DELETE VIDEO#################################################################


def extract_hls_prefix(hls_master_key):
    """
    Extracts the S3 prefix (folder) from the HLS master playlist key.
    """
    return '/'.join(hls_master_key.split('/')[:-1]) + '/'


def delete_hls_directory(s3_client, hls_master_key):
    """
    Delete all HLS files for a given master playlist from S3.
    """
    prefix = extract_hls_prefix(hls_master_key)
    try:
        response = s3_client.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Prefix=prefix
        )
        for obj in response.get('Contents', []):
            delete_s3_object(s3_client, obj['Key'])
    except Exception as e:
        print(f"Error deleting HLS files: {e}")


def delete_video_file(s3_client, video_key):
    """
    Delete original video file from S3 (e.g. videos/abc.mp4).
    """
    try:
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=video_key
        )
    except Exception as e:
        print(f"Error deleting video file: {e}")


@job('default')
def delete_video_assets_from_s3(hls_master_key, thumbnail_key, video_file_key):
    """Delete video assets from S3 and export Video model."""
    s3_client = get_s3_client()

    if hls_master_key:
        delete_hls_directory(s3_client, hls_master_key)

    if thumbnail_key:
        delete_s3_object(s3_client, thumbnail_key)

    if video_file_key:
        delete_video_file(s3_client, video_file_key)

    export_model_to_s3(Video)


def export_userwatchhistory_task():
    """Export all UserWatchHistory records to S3 (scheduled task)."""
    print("ExportUserWatchHistoryTask RUNNING")
    export_model_to_s3(UserWatchHistory)
