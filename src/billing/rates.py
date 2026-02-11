from dataclasses import dataclass
from decimal import Decimal

from src.billing.models import PaymentMethod


@dataclass(frozen=True)
class CardRates:
    """Taxas de cartão — injetável para facilitar testes e mudanças futuras."""

    base: Decimal = Decimal("0.0399")  # 3.99% para 1x
    installment_base: Decimal = Decimal("0.0499")  # 4.99% base para parcelado
    installment_extra: Decimal = Decimal("0.02")  # +2% por parcela extra (a partir da 2ª)


@dataclass(frozen=True)
class PlatformRates:
    """Configuração central de taxas da plataforma. Essas configuraçoes poderiam esta na base de dados (POR ENQUANTO VOU DEIXAR AQUI MESMO)"""

    pix_rate: Decimal = Decimal("0")
    card: CardRates = CardRates()

    def get_rate(self, payment_method: str, installments: int) -> Decimal:
        if payment_method == PaymentMethod.PIX:
            return self.pix_rate

        if installments == 1:
            return self.card.base

        extra_installments = installments - 1
        return self.card.installment_base + (self.card.installment_extra * extra_installments)
