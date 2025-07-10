from django.db import models
from django.conf import settings
import time
import os
import random
import string


def video_file_upload_to(instance, filename):
    """Generate upload path with timestamp and random 7-char ID."""
    base, ext = os.path.splitext(filename)
    timestamp = int(time.time())
    random_id = ''.join(random.choices(
        string.ascii_lowercase + string.digits, k=7))
    return f"videos/{base}_{timestamp}_{random_id}{ext}"


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    duration = models.PositiveIntegerField(
        null=True, blank=True, help_text="Duration in seconds")
    video_file = models.FileField(upload_to=video_file_upload_to)
    thumbnail = models.CharField(
        max_length=500, null=True, blank=True)  # S3 key for thumbnail
    hls_playlist = models.CharField(
        max_length=500, null=True, blank=True)  # S3 key for HLS master playlist
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    genre = models.CharField(max_length=255, null=False, blank=False)

    def __str__(self):
        return self.title


class UserWatchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    progress = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} watched {self.video.title} up to {self.progress} seconds"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "video"], name="unique_user_video")
        ]
