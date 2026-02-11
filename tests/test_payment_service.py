from decimal import Decimal

import pytest
from injector import Injector

from src.billing.di import BillingModule
from src.billing.services.payment_service import PaymentService


@pytest.fixture
def payment_service():
    injector = Injector([BillingModule])
    return injector.get(PaymentService)


class TestPaymentServicePix:
    """Fluxo completo PIX — taxa zero, split 100%."""

    def test_pix_single_recipient(self, payment_service):
        result = payment_service.process(
            {
                "amount": "150.00",
                "payment_method": "pix",
                "installments": 1,
                "splits": [{"recipient_id": "producer_1", "role": "producer", "percent": 100}],
            }
        )

        assert result["gross_amount"] == Decimal("150.00")
        assert result["platform_fee_amount"] == Decimal("0.00")
        assert result["net_amount"] == Decimal("150.00")
        assert len(result["receivables"]) == 1
        assert result["receivables"][0]["amount"] == Decimal("150.00")


class TestPaymentServiceCard:
    """Fluxo completo CARD — taxa + split."""

    def test_card_3x_70_30_from_spec(self, payment_service):
        """Exemplo exato do desafio."""
        result = payment_service.process(
            {
                "amount": "297.00",
                "payment_method": "card",
                "installments": 3,
                "splits": [
                    {"recipient_id": "producer_1", "role": "producer", "percent": 70},
                    {"recipient_id": "affiliate_9", "role": "affiliate", "percent": 30},
                ],
            }
        )

        assert result["gross_amount"] == Decimal("297.00")
        assert result["platform_fee_amount"] == Decimal("26.70")
        assert result["net_amount"] == Decimal("270.30")

        receivables = {r["recipient_id"]: r["amount"] for r in result["receivables"]}
        assert receivables["producer_1"] == Decimal("189.21")
        assert receivables["affiliate_9"] == Decimal("81.09")

    def test_receivables_sum_equals_net(self, payment_service):
        """Invariante: soma dos receivables == net_amount."""
        result = payment_service.process(
            {
                "amount": "1000.00",
                "payment_method": "card",
                "installments": 6,
                "splits": [
                    {"recipient_id": "a", "role": "producer", "percent": 40},
                    {"recipient_id": "b", "role": "affiliate", "percent": 35},
                    {"recipient_id": "c", "role": "affiliate", "percent": 25},
                ],
            }
        )

        total = sum(r["amount"] for r in result["receivables"])
        assert total == result["net_amount"]
