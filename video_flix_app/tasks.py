import os
import subprocess
import django_rq
from django_rq import job
from video_flix_app.models import Video, VideoResolution

# --- 1. Thumbnail-Task ---


@job('default')
def generate_thumbnail(video_path):
    """
    Erzeugt ein Vorschaubild des Videos und gibt den relativen URL-Pfad zurück.
    """
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

    return f"/media/thumbnails/{thumb_filename}"


# --- 2. Transcode-Task ---

@job('default')
def transcode_video(video_path, target_height, video_id=None):
    """
    Transcodiert das Video auf eine bestimmte Höhe (Vertikal-Auflösung),
    behält dabei das Seitenverhältnis bei und speichert das Ergebnis als VideoResolution.
    """
    base, ext = os.path.splitext(os.path.basename(video_path))
    out_dir = os.path.join('media', 'videos', f'{target_height}p')
    os.makedirs(out_dir, exist_ok=True)

    filename = f"{base}_{target_height}p{ext}"
    out_path = os.path.join(out_dir, filename)

    subprocess.run([
        'ffmpeg', '-i', video_path,
        '-vf', f"scale=-2:{target_height}",
        '-c:a', 'copy',  # Audio-Paket kopieren
        out_path
    ], check=True)

    relative_url = f"/media/videos/{target_height}p/{filename}"

    # Optional: VideoResolution in der DB speichern
    if video_id:
        VideoResolution.objects.create(
            video_id=video_id,
            height=target_height,
            file=relative_url
        )

    return relative_url


# --- 3. Orchestrator-Task ---

@job('default')
def process_video_pipeline(video_path, video_id=None):
    """
    1) Thumbnail erstellen
    2) Für jede Auflösung einen Transcode-Job enqueuen
    """
    # 1) Thumbnail
    thumbnail_url = generate_thumbnail(video_path)

    if video_id:
        # Thumbnail-Pfad im Video-Model speichern
        Video.objects.filter(id=video_id).update(thumbnail=thumbnail_url)

    # 2) Transkodierungen
    target_heights = [120, 360, 720, 1080]
    queue = django_rq.get_queue('default')
    for h in target_heights:
        # Job mit video_id weitergeben, damit jeder Transcode speichern kann
        queue.enqueue(transcode_video, video_path, h, video_id)

    return {
        'thumbnail': thumbnail_url,
        'queued_resolutions': target_heights
    }
