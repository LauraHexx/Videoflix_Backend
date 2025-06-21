import os
import mimetypes

from django.http import FileResponse, HttpResponseNotFound
from django.conf import settings

from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from rest_framework.exceptions import ValidationError
from django.db import IntegrityError

from ..models import Video, UserWatchHistory
from .serializers import VideoSerializer, UserWatchHistorySerializer


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [AllowAny]


class UserWatchHistoryViewSet(viewsets.ModelViewSet):
    queryset = UserWatchHistory.objects.all()
    serializer_class = UserWatchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        video_id = self.request.query_params.get("video")
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        return queryset.order_by('-updated_at')

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError(
                "You already have a watch history entry for this video.")

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("Only admins can delete watch history.")
        return super().destroy(request, *args, **kwargs)
