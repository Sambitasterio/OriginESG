from django.contrib import admin

from .models import DataSource, Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "source_type", "is_active", "created_at")
    list_filter = ("source_type", "is_active", "organization")
