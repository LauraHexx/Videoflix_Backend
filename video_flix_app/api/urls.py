from django.urls import path, include
from rest_framework import routers
from .views import VideoListView, VideoDetailView

router = routers.DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')

urlpatterns = [
    path('', include(router.urls)),
]
