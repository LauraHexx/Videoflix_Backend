from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import UserWatchHistory, Video


class VideoResource(resources.ModelResource):

    class Meta:
        model = Video


@admin.register(Video)
class VideoAdmin(ImportExportModelAdmin):
    resource_classes = [Video]


class UserWatchHistoryResource(resources.ModelResource):

    class Meta:
        model = UserWatchHistory


@admin.register(UserWatchHistory)
class UserWatchHistoryAdmin(ImportExportModelAdmin):
    resource_classes = [UserWatchHistory]
