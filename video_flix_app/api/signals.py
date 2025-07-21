from django.db.models.signals import post_save, post_delete
from django.core.cache import cache
from datetime import datetime, timezone
import time
from django.dispatch import receiver
import django_rq
from video_flix_app.models import Video, UserWatchHistory
from video_flix_app.api.tasks import process_video_pipeline, delete_video_assets_from_s3
from utils.export_utils import export_model_to_s3


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    """
    Enqueue video processing job after upload.
    Adds a short delay to avoid cold-start issues with RQ worker.
    """
    if created and instance.video_file:
        s3_key = instance.video_file.name

        queue = django_rq.get_queue('default')
        queue.enqueue(process_video_pipeline, s3_key, instance.id)


@receiver(post_delete, sender=Video)
def enqueue_video_deletion(sender, instance, **kwargs):
    """
    Enqueue deletion of thumbnail, video file and HLS files in S3 when a Video is deleted.
    """
    hls_key = instance.hls_playlist
    thumbnail_key = instance.thumbnail
    video_file_key = instance.video_file.name

    queue = django_rq.get_queue('default')
    queue.enqueue(delete_video_assets_from_s3, hls_key,
                  thumbnail_key, video_file_key)


@receiver(post_save, sender=Video)
def export_video_on_save(sender, instance, created, **kwargs):
    """Export Video data after update."""
    if not created:
        export_model_to_s3(Video)


EXPORT_CACHE_KEY = "userwatchhistory_last_export"


@receiver(post_save, sender=UserWatchHistory)
def export_userwatchhistory_hourly(sender, instance, **kwargs):
    """
    Export all UserWatchHistory records to S3 at most once per hour.
    This signal handler checks the timestamp of the last export (stored in cache).
    If the last export was more than one hour ago, it triggers a new export and updates the timestamp.
    """
    last_export = cache.get(EXPORT_CACHE_KEY)
    now = datetime.now(timezone.utc)
    if not last_export or (now - last_export).total_seconds() > 3600:
        export_model_to_s3(UserWatchHistory)
        cache.set(EXPORT_CACHE_KEY, now, timeout=None)
