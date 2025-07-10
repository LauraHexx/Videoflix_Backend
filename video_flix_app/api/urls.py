from django.urls import path, include
from rest_framework import routers
from .views import VideoViewSet, UserWatchHistoryViewSet, UniqueGenresAPIView

router = routers.DefaultRouter()
router.register(r'video', VideoViewSet, basename='video')
router.register(r'userwatchhistory', UserWatchHistoryViewSet,
                basename='userwatchhistory')

urlpatterns = [
    path('', include(router.urls)),
    path('genres/', UniqueGenresAPIView.as_view(), name='unique-genres'),
]
