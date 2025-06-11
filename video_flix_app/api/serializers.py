from rest_framework import serializers
from ..models import Video, UserWatchHistory


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = '__all__'


class UserWatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserWatchHistory
        fields = '__all__'
