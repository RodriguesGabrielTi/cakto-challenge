from django.db import models

from src.billing.constants import PAYMENT_METHOD_CARD, PAYMENT_METHOD_PIX
from src.common.models import BaseModel


class PaymentStatus(models.TextChoices):
    CAPTURED = "captured", "Captured"


class PaymentMethod(models.TextChoices):
    PIX = PAYMENT_METHOD_PIX, "PIX"
    CARD = PAYMENT_METHOD_CARD, "CARD"


class Payment(BaseModel):
    status = models.CharField(max_length=20, choices=PaymentStatus, default=PaymentStatus.CAPTURED)
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2)
    platform_fee_amount = models.DecimalField(max_digits=12, decimal_places=2)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod)
    installments = models.PositiveSmallIntegerField(default=1)
    idempotency_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment {self.id} - {self.gross_amount} BRL"


class LedgerEntry(BaseModel):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="ledger_entries")
    recipient_id = models.CharField(max_length=255)
    role = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_entries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ledger {self.recipient_id} - {self.amount} BRL"
