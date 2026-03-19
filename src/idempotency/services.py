import hashlib
import json
from dataclasses import dataclass
from typing import Optional

from injector import inject, singleton

from src.idempotency.models import IdempotencyRecord, IdempotencyStatus
from src.idempotency.repositories import IdempotencyRepository


@dataclass(frozen=True)
class IdempotencyResult:
    is_duplicate: bool
    is_conflict: bool
    record: Optional[IdempotencyRecord] = None
    cached_response: Optional[dict] = None


@singleton
class IdempotencyService:
    """
    Controle de idempotência com SHA-256 do payload.

    Fluxo:
    - Chave nova: processa normalmente, salva resposta ao final
    - Chave existente + mesmo hash: retorna resposta cacheada
    - Chave existente + hash diferente: conflito
    """

    @inject
    def __init__(self, repository: IdempotencyRepository):
        self._repository = repository

    @staticmethod
    def hash_payload(data: dict) -> str:
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def check(self, key: str, payload_hash: str) -> IdempotencyResult:
        """
        Verifica idempotência dentro de uma transação com lock.
        Deve ser chamado dentro de transaction.atomic().
        """
        record = self._repository.get_by_key_for_update(key)

        if record is None:
            new_record = self._repository.create(key, payload_hash)
            return IdempotencyResult(is_duplicate=False, is_conflict=False, record=new_record)

        if record.payload_hash != payload_hash:
            return IdempotencyResult(is_duplicate=False, is_conflict=True)

        # Mesma chave, mesmo payload - retorna resposta cacheada se disponível
        if record.status == IdempotencyStatus.COMPLETED:
            return IdempotencyResult(
                is_duplicate=True,
                is_conflict=False,
                cached_response=record.response_data,
            )

        # Ainda processando (request concorrente) - trata como duplicata sem cache
        return IdempotencyResult(is_duplicate=True, is_conflict=False)

    def save_response(self, record: IdempotencyRecord, response_data: dict) -> None:
        """Salva a resposta no registro de idempotência já existente (sem query extra)."""
        self._repository.mark_completed(record, response_data)
