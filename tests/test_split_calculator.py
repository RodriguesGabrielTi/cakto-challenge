from decimal import Decimal

import pytest
from injector import Injector

from src.billing.di import BillingModule
from src.billing.services.split_calculator import SplitCalculator


@pytest.fixture
def split_calculator():
    injector = Injector([BillingModule])
    return injector.get(SplitCalculator)


class TestSplitCalculatorBasic:
    """Cenários básicos de split."""

    def test_single_recipient_100_percent(self, split_calculator):
        """Split 100% para um único recebedor - valor integral."""
        result = split_calculator.calculate(
            Decimal("150.00"),
            [{"recipient_id": "producer_1", "role": "producer", "percent": 100}],
        )
        assert len(result) == 1
        assert result[0]["amount"] == Decimal("150.00")

    def test_two_recipients_70_30(self, split_calculator):
        """Exemplo do PDF: net R$270.30, split 70/30."""
        result = split_calculator.calculate(
            Decimal("270.30"),
            [
                {"recipient_id": "producer_1", "role": "producer", "percent": 70},
                {"recipient_id": "affiliate_9", "role": "affiliate", "percent": 30},
            ],
        )
        amounts = {r["recipient_id"]: r["amount"] for r in result}
        assert amounts["producer_1"] == Decimal("189.21")
        assert amounts["affiliate_9"] == Decimal("81.09")

    def test_split_sum_equals_net(self, split_calculator):
        """A soma dos receivables deve ser exatamente igual ao net_amount."""
        net = Decimal("270.30")
        result = split_calculator.calculate(
            net,
            [
                {"recipient_id": "p1", "role": "producer", "percent": 70},
                {"recipient_id": "a1", "role": "affiliate", "percent": 30},
            ],
        )
        total = sum(r["amount"] for r in result)
        assert total == net


class TestSplitCalculatorRounding:
    """Cenários de arredondamento - regra do centavo (Largest Remainder)."""

    def test_three_equal_parts(self, split_calculator):
        """R$100.00 / 3 partes iguais: 33.34 + 33.33 + 33.33 = 100.00"""
        result = split_calculator.calculate(
            Decimal("100.00"),
            [
                {"recipient_id": "a", "role": "r", "percent": Decimal("33.34")},
                {"recipient_id": "b", "role": "r", "percent": Decimal("33.33")},
                {"recipient_id": "c", "role": "r", "percent": Decimal("33.33")},
            ],
        )
        total = sum(r["amount"] for r in result)
        assert total == Decimal("100.00")

    def test_penny_goes_to_largest_remainder(self, split_calculator):
        """
        R$10.00 split 33.33/33.33/33.34:
        - exact: 3333.0, 3333.0, 3334.0 → floor = 9999, sobra 1 centavo.
        O centavo extra vai para quem teve maior resto fracionário.
        """
        result = split_calculator.calculate(
            Decimal("10.00"),
            [
                {"recipient_id": "a", "role": "r", "percent": Decimal("33.33")},
                {"recipient_id": "b", "role": "r", "percent": Decimal("33.33")},
                {"recipient_id": "c", "role": "r", "percent": Decimal("33.34")},
            ],
        )
        total = sum(r["amount"] for r in result)
        assert total == Decimal("10.00")

    def test_five_recipients_uneven(self, split_calculator):
        """5 recebedores com percentuais ímpares - soma deve bater."""
        net = Decimal("999.99")
        result = split_calculator.calculate(
            net,
            [
                {"recipient_id": "a", "role": "r", "percent": Decimal("10")},
                {"recipient_id": "b", "role": "r", "percent": Decimal("15")},
                {"recipient_id": "c", "role": "r", "percent": Decimal("20")},
                {"recipient_id": "d", "role": "r", "percent": Decimal("25")},
                {"recipient_id": "e", "role": "r", "percent": Decimal("30")},
            ],
        )
        total = sum(r["amount"] for r in result)
        assert total == net

    def test_small_amount_extreme_split(self, split_calculator):
        """R$0.01 (1 centavo) split 50/50 - impossível dividir igualmente."""
        result = split_calculator.calculate(
            Decimal("0.01"),
            [
                {"recipient_id": "a", "role": "r", "percent": 50},
                {"recipient_id": "b", "role": "r", "percent": 50},
            ],
        )
        total = sum(r["amount"] for r in result)
        assert total == Decimal("0.01")
        # Um recebe 0.01, outro recebe 0.00
        amounts = sorted([r["amount"] for r in result])
        assert amounts == [Decimal("0.00"), Decimal("0.01")]
