from injector import Binder, Module

from src.billing.rates import PlatformRates
from src.billing.services.fee_calculator import FeeCalculator
from src.billing.services.payment_service import PaymentService
from src.billing.services.split_calculator import SplitCalculator


class BillingModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(PlatformRates, to=PlatformRates())
        binder.bind(FeeCalculator, to=FeeCalculator)
        binder.bind(SplitCalculator, to=SplitCalculator)
        binder.bind(PaymentService, to=PaymentService)
