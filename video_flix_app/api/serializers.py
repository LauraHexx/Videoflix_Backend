from rest_framework import serializers
from django.conf import settings
from ..models import Video, UserWatchHistory, VideoResolution


class VideoResolutionSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = VideoResolution
        fields = ['height', 'file', 'file_url']
        read_only_fields = ['height', 'file']

    def get_file_url(self, obj):
        """Generate full S3 URL for video file."""
        if obj.file:
            return f"{settings.MEDIA_URL}{obj.file}"
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
        """Generate full S3 URL for thumbnail."""
        if obj.thumbnail:
            return f"{settings.MEDIA_URL}{obj.thumbnail}"
        return None


class UserWatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWatchHistory
        fields = ['id', 'user', 'video', 'progress', 'updated_at']
        read_only_fields = ['id', 'user']
