from decimal import ROUND_HALF_UP, Decimal

from injector import inject, singleton

from src.billing.rates import PlatformRates
from src.common.constants import DECIMAL_PRECISION, ZERO


@singleton
class FeeCalculator:
    """Calcula a taxa da plataforma sobre o valor bruto."""

    @inject
    def __init__(self, rates: PlatformRates):
        self._rates = rates

    def calculate(self, gross_amount: Decimal, payment_method: str, installments: int) -> Decimal:
        """
        PIX: 0%
        CARD 1x: 3.99%
        CARD 2-12x: 4.99% + 2% por parcela extra (ex: 3x = 4.99% + 4% = 8.99%)
        Este valor pode ser alterado atraves do rates injetado no construtor
        """
        rate = self._rates.get_rate(payment_method, installments)

        if rate == ZERO:
            return ZERO

        fee = gross_amount * rate
        return fee.quantize(DECIMAL_PRECISION, rounding=ROUND_HALF_UP)
