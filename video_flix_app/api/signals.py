from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from video_flix_app.models import Video
from video_flix_app.api.tasks import process_video_pipeline, delete_video_assets_from_s3
import django_rq


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    if created and instance.video_file:
        # Get S3 key from the file field
        s3_key = instance.video_file.name

        # Enqueue the video processing pipeline
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
