from decimal import Decimal

import pytest
from injector import Injector

from src.billing.constants import PAYMENT_METHOD_CARD, PAYMENT_METHOD_PIX
from src.billing.di import BillingModule
from src.billing.services.fee_calculator import FeeCalculator


@pytest.fixture
def fee_calculator():
    injector = Injector([BillingModule])
    return injector.get(FeeCalculator)


class TestFeeCalculatorPix:
    """PIX deve ter taxa zero independente do valor."""

    def test_pix_zero_fee(self, fee_calculator):
        fee = fee_calculator.calculate(Decimal("150.00"), PAYMENT_METHOD_PIX, 1)
        assert fee == Decimal("0.00")

    def test_pix_high_value_still_zero(self, fee_calculator):
        fee = fee_calculator.calculate(Decimal("99999.99"), PAYMENT_METHOD_PIX, 1)
        assert fee == Decimal("0.00")


class TestFeeCalculatorCard:
    """CARD 1x = 3.99%, 2-12x = 4.99% + 2% por parcela extra."""

    def test_card_1x(self, fee_calculator):
        # 100.00 * 3.99% = 3.99
        fee = fee_calculator.calculate(Decimal("100.00"), PAYMENT_METHOD_CARD, 1)
        assert fee == Decimal("3.99")

    def test_card_2x(self, fee_calculator):
        # 100.00 * (4.99% + 2%) = 6.99
        fee = fee_calculator.calculate(Decimal("100.00"), PAYMENT_METHOD_CARD, 2)
        assert fee == Decimal("6.99")

    def test_card_3x_example_from_spec(self, fee_calculator):
        """Exemplo do PDF: R$297.00 CARD 3x → taxa = R$26.70"""
        # 297.00 * (4.99% + 4%) = 297.00 * 8.99% = 26.7003 → 26.70
        fee = fee_calculator.calculate(Decimal("297.00"), PAYMENT_METHOD_CARD, 3)
        assert fee == Decimal("26.70")

    def test_card_12x(self, fee_calculator):
        # 100.00 * (4.99% + 22%) = 26.99
        fee = fee_calculator.calculate(Decimal("100.00"), PAYMENT_METHOD_CARD, 12)
        assert fee == Decimal("26.99")

    def test_card_rounding_half_up(self, fee_calculator):
        """Garante ROUND_HALF_UP: 0.005 arredonda para 0.01, não para 0.00."""
        # 1.00 * 3.99% = 0.0399 → 0.04 (ROUND_HALF_UP)
        fee = fee_calculator.calculate(Decimal("1.00"), PAYMENT_METHOD_CARD, 1)
        assert fee == Decimal("0.04")
