from django.urls import path

from src.billing.api.views import PaymentView

urlpatterns = [
    path("payments", PaymentView.as_view(), name="payment-create"),
]
