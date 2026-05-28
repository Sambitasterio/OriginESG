from django.conf import settings
from django.db import models

from organizations.models import DataSource


class IngestionRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETE = "COMPLETE", "Complete"
        FAILED = "FAILED", "Failed"

    data_source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, related_name="ingestion_runs"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    # SHA-256 of uploaded file — used to reject duplicate uploads
    file_hash = models.CharField(max_length=64, blank=True, null=True, unique=True)
    records_created = models.PositiveIntegerField(default=0)
    records_failed = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="ingestion_runs",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.data_source.name} run #{self.pk} [{self.status}]"


class RawRecord(models.Model):
    ingestion_run = models.ForeignKey(
        IngestionRun, on_delete=models.CASCADE, related_name="raw_records"
    )
    # Original ID from the source system (SAP doc number, meter ID row, etc.)
    source_row_id = models.CharField(max_length=255, blank=True)
    # Immutable snapshot — exactly what the source returned, never modified
    raw_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RawRecord #{self.pk} (run #{self.ingestion_run_id})"


class NormalizedRecord(models.Model):
    class GHGScope(models.IntegerChoices):
        SCOPE_1 = 1, "Scope 1 — Direct Combustion"
        SCOPE_2 = 2, "Scope 2 — Purchased Electricity"
        SCOPE_3 = 3, "Scope 3 — Value Chain"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        FLAGGED = "FLAGGED", "Flagged"
        LOCKED = "LOCKED", "Locked"

    # One normalized record per raw record
    raw_record = models.OneToOneField(
        RawRecord, on_delete=models.CASCADE, related_name="normalized"
    )

    # What the source actually reported
    original_value = models.DecimalField(max_digits=18, decimal_places=6)
    original_unit = models.CharField(max_length=50)

    # Always stored as kg CO2e after normalization
    normalized_value = models.DecimalField(max_digits=18, decimal_places=6)
    normalized_unit = models.CharField(max_length=20, default="kg_CO2e")

    # GHG classification
    ghg_scope = models.PositiveSmallIntegerField(choices=GHGScope.choices)
    # Human-readable activity label, e.g. "diesel_combustion", "electricity_uk_grid"
    activity_type = models.CharField(max_length=100)

    # Emission factor applied (stored so a future factor change doesn't silently alter history)
    emission_factor_used = models.DecimalField(max_digits=18, decimal_places=8)
    emission_factor_source = models.CharField(max_length=100)  # e.g. "DEFRA_2023"

    # Reporting period (billing periods may not align to calendar months)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"NormalizedRecord #{self.pk} [{self.status}] {self.normalized_value} kg CO2e"
