from django.db.models.signals import post_save
from django.dispatch import receiver
from video_flix_app.models import Video
from video_flix_app.tasks import process_video_pipeline


@receiver(post_save, sender=Video)
def enqueue_video_processing(sender, instance, created, **kwargs):
    if created:
        process_video_pipeline.delay(instance.video_file.path, instance.id)
