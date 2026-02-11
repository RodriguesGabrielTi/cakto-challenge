from decimal import Decimal

from django.db import transaction
from injector import inject, singleton

from src.billing.constants import (
    EXPECTED_PERCENT_SUM,
    MAX_INSTALLMENTS,
    MAX_PERCENT,
    MAX_SPLITS,
    MIN_INSTALLMENTS,
    MIN_PERCENT,
    MIN_SPLITS,
    PAYMENT_CAPTURED_EVENT,
    PAYMENT_METHOD_CARD,
    PAYMENT_METHOD_PIX,
    SUPPORTED_CURRENCIES,
)
from src.billing.repositories.payment_repository import PaymentRepository
from src.billing.services.fee_calculator import FeeCalculator
from src.billing.services.split_calculator import SplitCalculator
from src.common.exceptions import BusinessValidationError, ConflictError
from src.idempotency.services import IdempotencyService
from src.outbox.repositories.outbox_repository import OutboxRepository


@singleton
class PaymentService:
    @inject
    def __init__(
        self,
        fee_calculator: FeeCalculator,
        split_calculator: SplitCalculator,
        payment_repository: PaymentRepository,
        outbox_repository: OutboxRepository,
        idempotency_service: IdempotencyService,
    ):
        self._fee_calculator = fee_calculator
        self._split_calculator = split_calculator
        self._payment_repo = payment_repository
        self._outbox_repo = outbox_repository
        self._idempotency = idempotency_service

    def _validate(self, data: dict) -> None:
        """
        Validações de regra de negócio.
        Raises BusinessValidationError com dict de erros por campo.
        """
        errors = {}

        amount = Decimal(str(data.get("amount", 0)))
        if amount <= 0:
            errors["amount"] = "O valor deve ser maior que zero."

        currency = data.get("currency", "")
        if currency.upper() not in SUPPORTED_CURRENCIES:
            errors["currency"] = f"Moeda não suportada. Use: {', '.join(SUPPORTED_CURRENCIES)}."

        payment_method = data.get("payment_method")
        installments = data.get("installments", 1)

        if payment_method == PAYMENT_METHOD_PIX and installments != MIN_INSTALLMENTS:
            errors["installments"] = "PIX não aceita parcelamento."

        if payment_method == PAYMENT_METHOD_CARD:
            if installments < MIN_INSTALLMENTS or installments > MAX_INSTALLMENTS:
                errors["installments"] = f"Cartão aceita entre {MIN_INSTALLMENTS} e {MAX_INSTALLMENTS} parcelas."

        splits = data.get("splits", [])
        if len(splits) < MIN_SPLITS or len(splits) > MAX_SPLITS:
            errors["splits"] = f"Informe entre {MIN_SPLITS} e {MAX_SPLITS} recebedores."
        else:
            for i, s in enumerate(splits):
                percent = s.get("percent", 0)
                if percent <= MIN_PERCENT or percent > MAX_PERCENT:
                    errors[f"splits[{i}].percent"] = (
                        f"Percentual deve ser entre {MIN_PERCENT} (exclusivo) e {MAX_PERCENT}."
                    )

            total_percent = sum(s.get("percent", 0) for s in splits)
            if total_percent != EXPECTED_PERCENT_SUM:
                errors["splits"] = f"A soma dos percentuais deve ser {EXPECTED_PERCENT_SUM}%. Atual: {total_percent}%."

        if errors:
            raise BusinessValidationError(errors)

    def calculate(self, data: dict) -> dict:
        """Calcula taxas e split sem persistir - usado pelo endpoint /quote."""
        self._validate(data)

        gross_amount = Decimal(str(data["amount"]))
        payment_method = data["payment_method"]
        installments = data.get("installments", 1)

        fee = self._fee_calculator.calculate(gross_amount, payment_method, installments)
        net_amount = gross_amount - fee
        receivables = self._split_calculator.calculate(net_amount, data["splits"])

        return {
            "gross_amount": gross_amount,
            "platform_fee_amount": fee,
            "net_amount": net_amount,
            "receivables": receivables,
        }

    def process(self, data: dict, idempotency_key: str) -> dict:
        """
        Orquestra idempotência + cálculo + persistência + outbox
        em uma única transação.
        """
        payload_hash = IdempotencyService.hash_payload(data)

        with transaction.atomic():
            idempotency_result = self._idempotency.check(idempotency_key, payload_hash)

            if idempotency_result.is_conflict:
                raise ConflictError("Idempotency-Key já utilizada com payload diferente.")

            if idempotency_result.is_duplicate and idempotency_result.cached_response:
                return idempotency_result.cached_response

            result = self.calculate(data)

            payment = self._payment_repo.create(
                gross_amount=result["gross_amount"],
                platform_fee_amount=result["platform_fee_amount"],
                net_amount=result["net_amount"],
                payment_method=data["payment_method"],
                installments=data.get("installments", 1),
                idempotency_key=idempotency_key,
            )

            self._payment_repo.create_ledger_entries(payment, result["receivables"])

            self._outbox_repo.create(
                event_type=PAYMENT_CAPTURED_EVENT,
                payload={
                    "payment_id": str(payment.id),
                    "gross_amount": str(result["gross_amount"]),
                    "net_amount": str(result["net_amount"]),
                },
            )

            response_data = {
                "payment_id": str(payment.id),
                "status": payment.status,
                "gross_amount": result["gross_amount"],
                "platform_fee_amount": result["platform_fee_amount"],
                "net_amount": result["net_amount"],
                "receivables": result["receivables"],
                "outbox_event": {
                    "type": PAYMENT_CAPTURED_EVENT,
                    "status": "pending",
                },
            }

            # Cache serializado (Decimal -> str) para o JSONField
            cache_data = {
                "payment_id": str(payment.id),
                "status": payment.status,
                "gross_amount": str(result["gross_amount"]),
                "platform_fee_amount": str(result["platform_fee_amount"]),
                "net_amount": str(result["net_amount"]),
                "receivables": [{**r, "amount": str(r["amount"])} for r in result["receivables"]],
                "outbox_event": {
                    "type": PAYMENT_CAPTURED_EVENT,
                    "status": "pending",
                },
            }

            self._idempotency.save_response(idempotency_result.record, cache_data)

        return response_data
