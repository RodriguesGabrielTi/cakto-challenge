from django.db import models

from src.common.models import BaseModel


class IdempotencyStatus(models.TextChoices):
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"


class IdempotencyRecord(BaseModel):
    """
    Registro de idempotência para evitar processamento duplicado.
    O payload_hash (SHA-256) garante que a mesma chave não seja
    reutilizada com um payload diferente.
    """

    key = models.CharField(max_length=255, unique=True)
    payload_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=IdempotencyStatus, default=IdempotencyStatus.PROCESSING)
    response_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "idempotency_records"

    def __str__(self):
        return f"Idempotency {self.key} - {self.status}"
