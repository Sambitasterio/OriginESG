from django.conf import settings
from django.db import models

from ingestion.models import NormalizedRecord


class ReviewAction(models.Model):
    class Action(models.TextChoices):
        APPROVE = "APPROVE", "Approved"
        FLAG = "FLAG", "Flagged"
        UNFLAG = "UNFLAG", "Unflagged"
        LOCK = "LOCK", "Locked"

    normalized_record = models.ForeignKey(
        NormalizedRecord, on_delete=models.CASCADE, related_name="review_actions"
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    comment = models.TextField(blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="review_actions",
    )
    # Append-only — never update or delete rows; insert new ones instead
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.action} on record #{self.normalized_record_id} by {self.actor}"
