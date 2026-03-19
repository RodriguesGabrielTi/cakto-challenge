from django.db import models

from src.common.models import BaseModel


class OutboxEventStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PUBLISHED = "published", "Published"


class OutboxEvent(BaseModel):
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=OutboxEventStatus, default=OutboxEventStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "outbox_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"OutboxEvent {self.event_type} - {self.status}"
