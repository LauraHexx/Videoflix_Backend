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
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expiration
        )
        return response
    except ClientError:
        return None


class VideoResolutionSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = VideoResolution
        fields = ['height', 'file', 'file_url']
        read_only_fields = ['height', 'file']

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
    class Meta:
        model = UserWatchHistory
        fields = ['user', 'video', 'progress']
        read_only_fields = ['user', 'video']
