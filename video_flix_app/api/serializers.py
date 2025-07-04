from rest_framework import serializers
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
from ..models import Video, UserWatchHistory


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


def get_content_type(s3_key):
    """Return content type based on file extension."""
    ext = s3_key.lower()
    if ext.endswith('.mp4'):
        return 'video/mp4'
    elif ext.endswith('.webm'):
        return 'video/webm'
    elif ext.endswith('.ogg'):
        return 'video/ogg'
    elif ext.endswith('.mov'):
        return 'video/quicktime'
    elif ext.endswith('.avi'):
        return 'video/x-msvideo'
    elif ext.endswith(('.jpg', '.jpeg')):
        return 'image/jpeg'
    elif ext.endswith('.png'):
        return 'image/png'
    elif ext.endswith('.m3u8'):
        return 'application/vnd.apple.mpegurl'
    elif ext.endswith('.ts'):
        return 'video/mp2t'
    return 'application/octet-stream'


def build_presigned_url(s3_client, s3_key, content_type, expiration):
    """Generate and return a presigned URL for S3 object."""
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': s3_key,
                'ResponseContentDisposition': 'inline',
                'ResponseContentType': content_type
            },
            ExpiresIn=expiration
        )
    except ClientError:
        return None


def generate_presigned_url(s3_key, expiration=3600):
    """Generate a presigned URL for S3 object."""
    s3_client = get_s3_client()
    content_type = get_content_type(s3_key)
    return build_presigned_url(s3_client, s3_key, content_type, expiration)


class VideoSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    hls_playlist_url = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id", "title", "description", "duration", "video_file",
            "genre", "thumbnail", "thumbnail_url", "hls_playlist", "hls_playlist_url",
            "watch_progress",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "created_at", "duration",
            "thumbnail", "hls_playlist", "thumbnail_url", "hls_playlist_url", "watch_progress"
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return generate_presigned_url(obj.thumbnail)
        return None

    def get_hls_playlist_url(self, obj):
        if obj.hls_playlist:
            return generate_presigned_url(obj.hls_playlist)
        return None

    def get_watch_progress(self, obj):
        user_watch_history = getattr(obj, 'user_watch_history', [])
        if user_watch_history:
            return user_watch_history[0].progress
        return 0


class UserWatchHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for user-specific video watch history.
    Handles creation, update, and display of progress for each user and video.
    """
    video = VideoSerializer(read_only=True)
    video_id = serializers.PrimaryKeyRelatedField(
        queryset=Video.objects.all(), source='video', write_only=True
    )

    class Meta:
        model = UserWatchHistory
        fields = ['id', 'user', 'video', 'video_id', 'progress', 'updated_at']
        read_only_fields = ['id', 'user']

    def validate(self, data):
        """
        Ensure progress does not exceed video duration.
        """
        video = data.get('video') or self.instance.video
        progress = data.get('progress', getattr(self.instance, 'progress', 0))
        if video.duration is not None and progress > video.duration:
            raise serializers.ValidationError(
                "Progress cannot exceed video duration.")
        return data
