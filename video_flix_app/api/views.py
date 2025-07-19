from rest_framework.decorators import action
from django.db.models import Prefetch
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
import random


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
        cache_key = "random_video_id"
        random_id = cache.get(cache_key)
        video_ids = list(self.queryset.values_list('id', flat=True))
        if not video_ids:
            return Response({"detail": "No videos found."}, status=status.HTTP_404_NOT_FOUND)
        random_id = random.choice(video_ids)
        video = self.queryset.get(id=random_id)
        serializer = self.get_serializer(video)
        return Response(serializer.data)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Video.objects.prefetch_related(
                Prefetch(
                    'userwatchhistory_set',
                    queryset=UserWatchHistory.objects.filter(user=user),
                    to_attr='user_watch_history'
                )
            )
        return super().get_queryset()

    def destroy(self, request, *args, **kwargs):
        """
        Only admin users are allowed to delete videos.
        """
        if not request.user.is_staff:
            raise PermissionDenied("Only admins can delete videos.")
        return super().destroy(request, *args, **kwargs)


class UniqueGenresAPIView(APIView):
    """
    API endpoint that returns a list of unique genres from Video model.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        genres_qs = Video.objects \
            .exclude(genre__isnull=True) \
            .exclude(genre__exact='') \
            .order_by('genre') \
            .values_list('genre', flat=True) \
            .distinct()
        genres = list(genres_qs)
        return Response({'genres': genres})


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
        Creates or updates watch history entry for the current user and video.
        If an entry already exists, it updates the progress instead of failing.
        """
        user = self.request.user
        video = serializer.validated_data["video"]
        progress = serializer.validated_data.get("progress", 0)

        instance, created = UserWatchHistory.objects.update_or_create(
            user=user,
            video=video,
            defaults={"progress": progress}
        )
        serializer.instance = instance

    def destroy(self, request, *args, **kwargs):
        """
        Allows only admin users to delete watch history entries.
        """
        if not request.user.is_staff:
            raise PermissionDenied("Only admins can delete watch history.")
        return super().destroy(request, *args, **kwargs)
