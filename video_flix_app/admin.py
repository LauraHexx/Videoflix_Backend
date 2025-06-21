from django.contrib import admin
from .models import UserWatchHistory


class UserWatchHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "video",
        "progress",
        "updated_at",
    ]


admin.site.register(UserWatchHistory, UserWatchHistoryAdmin)
