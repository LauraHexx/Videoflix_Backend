from django.db.models.signals import post_save
from django.dispatch import receiver
from video_flix_app.models import Video
from video_flix_app.tasks import process_video_pipeline
import django_rq


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    if created and instance.video_file:
        # Get S3 key from the file field
        s3_key = instance.video_file.name

        # Enqueue the video processing pipeline
        queue = django_rq.get_queue('default')
        queue.enqueue(process_video_pipeline, s3_key, instance.id)
