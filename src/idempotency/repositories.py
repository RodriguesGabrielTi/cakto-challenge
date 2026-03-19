from typing import Optional

from injector import singleton

from src.idempotency.models import IdempotencyRecord, IdempotencyStatus


@singleton
class IdempotencyRepository:
    def get_by_key_for_update(self, key: str) -> Optional[IdempotencyRecord]:
        """Busca registro com lock pessimista (SELECT FOR UPDATE)."""
        return IdempotencyRecord.objects.select_for_update().filter(key=key).first()

    def create(self, key: str, payload_hash: str) -> IdempotencyRecord:
        return IdempotencyRecord.objects.create(
            key=key,
            payload_hash=payload_hash,
            status=IdempotencyStatus.PROCESSING,
        )

    def mark_completed(self, record: IdempotencyRecord, response_data: dict) -> None:
        record.status = IdempotencyStatus.COMPLETED
        record.response_data = response_data
        record.save(update_fields=["status", "response_data"])
