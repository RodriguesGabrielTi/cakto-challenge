import uuid

from django.db import models


class BaseModel(models.Model):
    """Model base abstrato com UUID v4 como primary key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
