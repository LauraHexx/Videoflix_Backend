from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import CustomUser

# Register your models here.


class CustomUserResource(resources.ModelResource):
    """
    Resource class for import/export of CustomUser model data.
    Used by django-import-export for admin actions.
    """
    class Meta:
        model = CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin):
    """
    Admin configuration for CustomUser model.
    Enables import/export and displays all fields in the admin list view.
    """
    resource_classes = [CustomUserResource]
    list_display = [field.name for field in CustomUser._meta.fields]
