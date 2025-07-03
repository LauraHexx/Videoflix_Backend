from rest_framework.decorators import action
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
import random

from rest_framework.exceptions import ValidationError
from django.db import IntegrityError

from ..models import Video, UserWatchHistory
from .serializers import VideoSerializer, UserWatchHistorySerializer


class VideoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing video objects.
    Provides full CRUD access to all videos (no authentication required).
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='random')
    def random_video(self, request):
        """Returns a random video."""
        video_ids = list(self.queryset.values_list('id', flat=True))
        if not video_ids:
            return Response({"detail": "No videos found."}, status=status.HTTP_404_NOT_FOUND)
        random_id = random.choice(video_ids)
        video = self.queryset.get(id=random_id)
        serializer = self.get_serializer(video)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Only admin users are allowed to delete videos.
        """
        if not request.user.is_staff:
            raise PermissionDenied("Only admins can delete videos.")
        return super().destroy(request, *args, **kwargs)


class UserWatchHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user-specific video watch history.
    """

    queryset = UserWatchHistory.objects.all()
    serializer_class = UserWatchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return queryset filtered by current user unless staff.
        Optionally filter by video ID and order by last update descending.
        """
        user = self.request.user
        queryset = self.queryset
        if not user.is_staff:
            queryset = queryset.filter(user=user)
        video_id = self.request.query_params.get("video")
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        return queryset.order_by('-updated_at')

    def perform_create(self, serializer):
        """
        Sets the current user automatically when creating a new entry.
        Raises a validation error if an entry for this user and video already exists.
        """
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError(
                "You already have a watch history entry for this video.")

    def destroy(self, request, *args, **kwargs):
        """
        Allows only admin users to delete watch history entries.
        """
        if not request.user.is_staff:
            raise PermissionDenied("Only admins can delete watch history.")
        return super().destroy(request, *args, **kwargs)
