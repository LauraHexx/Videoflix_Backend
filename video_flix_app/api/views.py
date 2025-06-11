from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import Video, UserWatchHistory
from .serializers import VideoSerializer, UserWatchHistorySerializer


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()


class UserWatchHistoryViewSet(viewsets.ModelViewSet):
    queryset = UserWatchHistory.objects.all()
    serializer_class = UserWatchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
