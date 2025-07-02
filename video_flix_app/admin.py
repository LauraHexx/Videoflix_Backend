from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import UserWatchHistory, Video


class VideoResource(resources.ModelResource):
    """
    Resource class for the Video model.
    Enables import and export functionality for all Video fields in the Django admin interface.
    """
    class Meta:
        model = Video


class UserWatchHistoryResource(resources.ModelResource):
    """
    Resource class for the UserWatchHistory model.
    Enables import and export functionality for all UserWatchHistory fields in the Django admin interface.
    """
    class Meta:
        model = UserWatchHistory


@admin.register(Video)
class VideoAdmin(ImportExportModelAdmin):
    """
    Admin configuration for the Video model.
    Displays all fields in the list view and enables import/export functionality.
    """
    resource_classes = [Video]
    list_display = [field.name for field in Video._meta.fields]


@admin.register(UserWatchHistory)
class UserWatchHistoryAdmin(ImportExportModelAdmin):
    """
    Admin configuration for the UserWatchHistory model.
    Displays all fields in the list view and enables import/export functionality.
    """
    resource_classes = [UserWatchHistory]
    list_display = [field.name for field in UserWatchHistory._meta.fields]
