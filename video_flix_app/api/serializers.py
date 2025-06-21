from rest_framework import serializers
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
from ..models import Video, UserWatchHistory, VideoResolution


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


def generate_presigned_url(s3_key, expiration=3600):
    """Generate a presigned URL for S3 object."""
    try:
        s3_client = get_s3_client()

        # Determine content type based on file extension
        content_type = 'application/octet-stream'  # default
        if s3_key.lower().endswith('.mp4'):
            content_type = 'video/mp4'
        elif s3_key.lower().endswith('.webm'):
            content_type = 'video/webm'
        elif s3_key.lower().endswith('.ogg'):
            content_type = 'video/ogg'
        elif s3_key.lower().endswith('.mov'):
            content_type = 'video/quicktime'
        elif s3_key.lower().endswith('.avi'):
            content_type = 'video/x-msvideo'
        elif s3_key.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif s3_key.lower().endswith('.png'):
            content_type = 'image/png'

        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': s3_key,
                'ResponseContentDisposition': 'inline',
                'ResponseContentType': content_type
            },
            ExpiresIn=expiration
        )
        return response
    except ClientError:
        return None


class VideoResolutionSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = VideoResolution
        fields = ['height', 'file_url']
        read_only_fields = ['height']

    def get_file_url(self, obj):
        """Generate presigned S3 URL for video file."""
        if obj.file:
            return generate_presigned_url(obj.file)
        return None


class VideoSerializer(serializers.ModelSerializer):
    resolutions = VideoResolutionSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id", "title", "description", "video_file",
            "genre", "thumbnail", "thumbnail_url", "resolutions",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "created_at",
            "thumbnail", "resolutions", "thumbnail_url"
        ]

    def get_thumbnail_url(self, obj):
        """Generate presigned S3 URL for thumbnail."""
        if obj.thumbnail:
            return generate_presigned_url(obj.thumbnail)
        return None


class UserWatchHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for user-specific video watch history.
    Handles creation, update, and display of progress for each user and video.
    """
    class Meta:
        model = UserWatchHistory
        fields = ['id', 'user', 'video', 'progress', 'updated_at']
        read_only_fields = ['id', 'user']
