from rest_framework import serializers
from ..models import Video, UserWatchHistory


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'video_file',
                  'thumbnail', 'created_at', 'updated_at', 'genre']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        return Video.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get(
            'description', instance.description)


class UserWatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWatchHistory
        fields = '__all__'
