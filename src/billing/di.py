from injector import Binder, Module

from src.billing.rates import PlatformRates
from src.billing.repositories.payment_repository import PaymentRepository
from src.billing.services.fee_calculator import FeeCalculator
from src.billing.services.payment_service import PaymentService
from src.billing.services.split_calculator import SplitCalculator
from src.idempotency.repositories import IdempotencyRepository
from src.idempotency.services import IdempotencyService
from src.outbox.repositories.outbox_repository import OutboxRepository


class BillingModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(PlatformRates, to=PlatformRates())
        binder.bind(FeeCalculator, to=FeeCalculator)
        binder.bind(SplitCalculator, to=SplitCalculator)
        binder.bind(PaymentRepository, to=PaymentRepository)
        binder.bind(OutboxRepository, to=OutboxRepository)
        binder.bind(IdempotencyRepository, to=IdempotencyRepository)
        binder.bind(IdempotencyService, to=IdempotencyService)
        binder.bind(PaymentService, to=PaymentService)
