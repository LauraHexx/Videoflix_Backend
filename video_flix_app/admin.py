from django.contrib import admin
from .models import UserWatchHistory, Video


class VideoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "description",
        "duration",
        "video_file",
        "thumbnail",
        "hls_playlist",
        "created_at",
        "updated_at",
        "genre",
    ]


class UserWatchHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "video",
        "progress",
        "updated_at",
    ]


admin.site.register(Video, VideoAdmin)
admin.site.register(UserWatchHistory, UserWatchHistoryAdmin)
