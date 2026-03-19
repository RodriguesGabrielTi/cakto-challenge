from injector import singleton

from src.outbox.models import OutboxEvent, OutboxEventStatus


@singleton
class OutboxRepository:

    def create(self, event_type: str, payload: dict) -> OutboxEvent:
        return OutboxEvent.objects.create(
            event_type=event_type,
            payload=payload,
            status=OutboxEventStatus.PENDING,
        )
