from django.db import models
from django.conf import settings


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    video_file = models.FileField(upload_to="videos/")
    thumbnail = models.CharField(
        max_length=500, null=True, blank=True)  # S3 key for thumbnail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    genre = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.title


class VideoResolution(models.Model):
    video = models.ForeignKey(
        Video, related_name='resolutions', on_delete=models.CASCADE)
    height = models.PositiveIntegerField()
    file = models.CharField(max_length=500)  # S3 key for video file

    def __str__(self):
        return f"{self.video.title} - {self.height}p"


class UserWatchHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    progress = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} watched {self.video.title} {self.progress}%"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "video"], name="unique_user_video")
        ]
