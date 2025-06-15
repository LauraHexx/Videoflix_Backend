from rest_framework import serializers
from ..models import Video, UserWatchHistory, VideoResolution


class VideoResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoResolution
        fields = ['height', 'file']
        read_only_fields = ['height']


class VideoSerializer(serializers.ModelSerializer):
    resolutions = VideoResolutionSerializer(
        many=True, read_only=True)
    thumbnail = serializers.ImageField(read_only=True)

    class Meta:
        model = Video
        fields = [
            "id", "title", "description", "video_file",
            "genre", "thumbnail", "resolutions",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "created_at", "updated_at",
            "thumbnail", "resolutions"
        ]

    def create(self, validated_data):
        video = Video.objects.create(
            title=validated_data["title"],
            description=validated_data.get("description", ""),
            video_file=validated_data["video_file"],
            genre=validated_data.get("genre", None),
            thumbnail=None
        )
        return video

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get(
            "description", instance.description)
        instance.genre = validated_data.get("genre", instance.genre)
        instance.save()
        return instance


class UserWatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWatchHistory
        fields = ['user', 'video', 'progress']
        read_only_fields = ['user', 'video']

    def create(self, validated_data):
        user = self.context['request'].user
        video = validated_data['video']
        progress = validated_data['progress']
        return UserWatchHistory.objects.create(
            user=user, video=video, progress=progress)
