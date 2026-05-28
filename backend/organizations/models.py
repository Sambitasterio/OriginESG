from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DataSource(models.Model):
    class SourceType(models.TextChoices):
        SAP = "SAP", "SAP OData"
        UTILITY = "UTILITY", "Utility / Green Button"
        TRAVEL = "TRAVEL", "Concur Travel"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="data_sources"
    )
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    # Stores API base URLs, grid region codes, etc. Never log this field.
    config = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization.name} — {self.name} ({self.source_type})"
