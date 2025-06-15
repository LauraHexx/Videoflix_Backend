from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from ..models import Video, UserWatchHistory
from .serializers import VideoSerializer, UserWatchHistorySerializer


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [AllowAny]


class UserWatchHistoryViewSet(viewsets.ModelViewSet):
    queryset = UserWatchHistory.objects.all()
    serializer_class = UserWatchHistorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
