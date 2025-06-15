import os
import subprocess
import django_rq
from django_rq import job
from video_flix_app.models import Video, VideoResolution


@job('default')
def generate_thumbnail(video_path):
    base, _ = os.path.splitext(os.path.basename(video_path))
    thumb_dir = os.path.join('media', 'thumbnails')
    os.makedirs(thumb_dir, exist_ok=True)

    thumb_filename = f"{base}.jpg"
    thumb_fullpath = os.path.join(thumb_dir, thumb_filename)

    subprocess.run([
        'ffmpeg', '-i', video_path,
        '-ss', '00:00:01',
        '-vframes', '1',
        thumb_fullpath
    ], check=True)

    return f"thumbnails/{thumb_filename}"


@job('default')
def transcode_video(video_path, target_height, video_id=None):
    base, ext = os.path.splitext(os.path.basename(video_path))
    out_dir = os.path.join('media', 'videos', f'{target_height}p')
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{base}_{target_height}p{ext}"
    out_path = os.path.join(out_dir, filename)

    subprocess.run([
        'ffmpeg', '-i', video_path,
        '-vf', f"scale=-2:{target_height}",
        '-c:a', 'copy',
    ], check=True)

    relative_url = f"videos/{target_height}p/{filename}"

    if video_id:
        VideoResolution.objects.create(
            video_id=video_id,
            height=target_height,
            file=relative_url
        )

    return relative_url


@job('default')
def process_video_pipeline(video_path, video_id=None):

    thumbnail_url = generate_thumbnail(video_path)

    if video_id:

        Video.objects.filter(id=video_id).update(thumbnail=thumbnail_url)

    target_heights = [120, 360, 720, 1080]
    queue = django_rq.get_queue('default')
    for h in target_heights:

        queue.enqueue(transcode_video, video_path, h, video_id)

    return {
        'thumbnail': thumbnail_url,
        'queued_resolutions': target_heights
    }
