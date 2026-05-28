from django.contrib import admin

from .models import IngestionRun, NormalizedRecord, RawRecord


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = (
        "id", "data_source", "status", "records_created",
        "records_failed", "triggered_by", "started_at",
    )
    list_filter = ("status", "data_source__source_type")
    readonly_fields = ("started_at", "completed_at", "file_hash")


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "ingestion_run", "source_row_id", "created_at")
    readonly_fields = ("raw_data", "created_at")


@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id", "ghg_scope", "activity_type", "original_value", "original_unit",
        "normalized_value", "emission_factor_source", "status", "period_start", "period_end",
    )
    list_filter = ("status", "ghg_scope", "emission_factor_source")
    readonly_fields = ("created_at", "updated_at")
