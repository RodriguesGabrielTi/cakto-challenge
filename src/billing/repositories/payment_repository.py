from decimal import Decimal

from injector import singleton

from src.billing.models import LedgerEntry, Payment, PaymentStatus


@singleton
class PaymentRepository:
    @staticmethod
    def create(
        gross_amount: Decimal,
        platform_fee_amount: Decimal,
        net_amount: Decimal,
        payment_method: str,
        installments: int,
        idempotency_key: str,
    ) -> Payment:
        return Payment.objects.create(
            status=PaymentStatus.CAPTURED,
            gross_amount=gross_amount,
            platform_fee_amount=platform_fee_amount,
            net_amount=net_amount,
            payment_method=payment_method,
            installments=installments,
            idempotency_key=idempotency_key,
        )

    @staticmethod
    def create_ledger_entries(payment: Payment, receivables: list[dict]) -> list[LedgerEntry]:
        entries = [
            LedgerEntry(
                payment=payment,
                recipient_id=r["recipient_id"],
                role=r["role"],
                amount=r["amount"],
            )
            for r in receivables
        ]
        return LedgerEntry.objects.bulk_create(entries)
