from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import CustomUser

# Register your models here.


class CustomUserResource(resources.ModelResource):
    class Meta:
        model = CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(ImportExportModelAdmin):
    resource_classes = [CustomUserResource]
