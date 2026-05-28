from django.contrib import admin

from .models import ReviewAction


@admin.register(ReviewAction)
class ReviewActionAdmin(admin.ModelAdmin):
    list_display = ("id", "normalized_record", "action", "actor", "created_at")
    list_filter = ("action",)
    readonly_fields = ("created_at",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
