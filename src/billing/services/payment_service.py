from decimal import Decimal

from injector import inject, singleton

from src.billing.services.fee_calculator import FeeCalculator
from src.billing.services.split_calculator import SplitCalculator


@singleton
class PaymentService:
    """Orquestra o fluxo de criação de pagamento."""

    @inject
    def __init__(self, fee_calculator: FeeCalculator, split_calculator: SplitCalculator):
        self._fee_calculator = fee_calculator
        self._split_calculator = split_calculator

    def process(self, data: dict) -> dict:
        """
        Recebe os dados validados do pagamento e retorna o resultado
        com taxa, valor líquido e split calculados.
        """
        gross_amount = Decimal(str(data["amount"]))
        payment_method = data["payment_method"]
        installments = data.get("installments", 1)
        splits = data["splits"]

        fee = self._fee_calculator.calculate(gross_amount, payment_method, installments)
        net_amount = gross_amount - fee
        receivables = self._split_calculator.calculate(net_amount, splits)

        return {
            "gross_amount": gross_amount,
            "platform_fee_amount": fee,
            "net_amount": net_amount,
            "receivables": receivables,
        }
