from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from src.billing.constants import CURRENCY_BRL
from src.billing.models import LedgerEntry, Payment
from src.outbox.models import OutboxEvent

ENDPOINT = "/api/v1/payments"


@pytest.fixture
def client():
    return APIClient()


def _make_payload(**overrides):
    """Payload base válido para o endpoint."""
    base = {
        "amount": "297.00",
        "currency": CURRENCY_BRL,
        "payment_method": "card",
        "installments": 3,
        "splits": [
            {"recipient_id": "producer_1", "role": "producer", "percent": 70},
            {"recipient_id": "affiliate_9", "role": "affiliate", "percent": 30},
        ],
    }
    base.update(overrides)
    return base


def _post(client, payload=None, key="default-key"):
    return client.post(
        ENDPOINT,
        payload or _make_payload(),
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )


@pytest.mark.django_db
class TestPaymentEndpoint:
    """Testes de integração do endpoint POST /api/v1/payments."""

    def test_create_payment_success(self, client):
        """Requisição válida retorna 201 com dados corretos."""
        response = _post(client, key="create-success")

        assert response.status_code == 201

        data = response.json()
        assert data["gross_amount"] == "297.00"
        assert data["platform_fee_amount"] == "26.70"
        assert data["net_amount"] == "270.30"
        assert len(data["receivables"]) == 2
        assert data["outbox_event"]["type"] == "payment_captured"
        assert data["outbox_event"]["status"] == "pending"

    def test_pix_payment_success(self, client):
        """PIX com taxa zero e split 100%."""
        payload = _make_payload(
            amount="150.00",
            payment_method="pix",
            installments=1,
            splits=[{"recipient_id": "p1", "role": "producer", "percent": 100}],
        )
        response = _post(client, payload, key="pix-success")

        assert response.status_code == 201
        data = response.json()
        assert data["platform_fee_amount"] == "0.00"
        assert data["net_amount"] == "150.00"
        assert data["receivables"][0]["amount"] == "150.00"

    def test_card_1x_payment_success(self, client):
        """CARD 1x usa taxa base (3.99%)."""
        payload = _make_payload(
            amount="100.00",
            installments=1,
            splits=[{"recipient_id": "p1", "role": "producer", "percent": 100}],
        )
        response = _post(client, payload, key="card-1x-success")

        assert response.status_code == 201
        data = response.json()
        assert data["platform_fee_amount"] == "3.99"
        assert data["net_amount"] == "96.01"

    def test_minimum_amount(self, client):
        """Valor mínimo (R$0.01) com split."""
        payload = _make_payload(
            amount="0.01",
            payment_method="pix",
            installments=1,
            splits=[{"recipient_id": "p1", "role": "producer", "percent": 100}],
        )
        response = _post(client, payload, key="min-amount")

        assert response.status_code == 201
        assert response.json()["net_amount"] == "0.01"

    def test_missing_idempotency_key_returns_400(self, client):
        response = client.post(ENDPOINT, _make_payload(), format="json")

        assert response.status_code == 400
        assert "Idempotency-Key" in response.json()["detail"]


@pytest.mark.django_db
class TestLedgerAndOutbox:
    """Verifica persistência de LedgerEntry e OutboxEvent no banco."""

    def test_ledger_entries_created(self, client):
        """Cada recebedor gera um LedgerEntry com valores corretos."""
        response = _post(client, key="ledger-test")
        payment_id = response.json()["payment_id"]

        entries = LedgerEntry.objects.filter(payment_id=payment_id).order_by("recipient_id")
        assert entries.count() == 2

        affiliate = entries.get(recipient_id="affiliate_9")
        producer = entries.get(recipient_id="producer_1")

        assert affiliate.role == "affiliate"
        assert affiliate.amount == Decimal("81.09")

        assert producer.role == "producer"
        assert producer.amount == Decimal("189.21")

    def test_ledger_sum_equals_net(self, client):
        """Soma dos ledger entries == net_amount do payment."""
        response = _post(client, key="ledger-sum")
        payment_id = response.json()["payment_id"]

        payment = Payment.objects.get(id=payment_id)
        ledger_total = sum(e.amount for e in LedgerEntry.objects.filter(payment_id=payment_id))

        assert ledger_total == payment.net_amount

    def test_outbox_event_created(self, client):
        """OutboxEvent criado com tipo e payload corretos."""
        response = _post(client, key="outbox-test")
        payment_id = response.json()["payment_id"]

        event = OutboxEvent.objects.latest("created_at")
        assert event.event_type == "payment_captured"
        assert event.status == "pending"
        assert event.payload["payment_id"] == payment_id
        assert event.payload["gross_amount"] == "297.00"
        assert event.payload["net_amount"] == "270.30"
        assert event.published_at is None


@pytest.mark.django_db
class TestIdempotency:
    """Testes de idempotência do endpoint."""

    def test_same_key_same_payload_returns_cached(self, client):
        """Mesma chave + mesmo payload retorna resposta cacheada sem duplicar."""
        payload = _make_payload()
        key = "idempotency-dup-test"

        first = _post(client, payload, key=key)
        second = _post(client, payload, key=key)

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["payment_id"] == second.json()["payment_id"]

        # Apenas 1 Payment no banco
        assert Payment.objects.filter(idempotency_key=key).count() == 1

    def test_same_key_different_payload_returns_409(self, client):
        """Mesma chave + payload diferente retorna 409 Conflict."""
        key = "idempotency-conflict-test"

        _post(client, _make_payload(amount="100.00"), key=key)
        response = _post(client, _make_payload(amount="999.00"), key=key)

        assert response.status_code == 409
        assert "Idempotency-Key" in response.json()["detail"]


@pytest.mark.django_db
class TestBusinessValidation:
    """Testes de validação de regras de negócio."""

    def test_negative_amount_returns_400(self, client):
        response = _post(client, _make_payload(amount="-10.00"), key="val-neg")

        assert response.status_code == 400
        assert "amount" in response.json()

    def test_zero_amount_returns_400(self, client):
        response = _post(client, _make_payload(amount="0.00"), key="val-zero")

        assert response.status_code == 400
        assert "amount" in response.json()

    def test_invalid_currency_returns_400(self, client):
        response = _post(client, _make_payload(currency="USD"), key="val-currency")

        assert response.status_code == 400
        assert "currency" in response.json()

    def test_pix_with_installments_returns_400(self, client):
        payload = _make_payload(payment_method="pix", installments=3)

        response = _post(client, payload, key="val-pix-inst")

        assert response.status_code == 400
        assert "installments" in response.json()

    def test_card_13_installments_returns_400(self, client):
        response = _post(client, _make_payload(installments=13), key="val-card-13")

        assert response.status_code == 400
        assert "installments" in response.json()

    def test_card_0_installments_returns_400(self, client):
        response = _post(client, _make_payload(installments=0), key="val-card-0")

        assert response.status_code == 400
        assert "installments" in response.json()

    def test_splits_not_summing_100_returns_400(self, client):
        payload = _make_payload(
            splits=[
                {"recipient_id": "a", "role": "producer", "percent": 50},
                {"recipient_id": "b", "role": "affiliate", "percent": 30},
            ]
        )

        response = _post(client, payload, key="val-split-sum")

        assert response.status_code == 400
        assert "splits" in response.json()

    def test_six_splits_returns_400(self, client):
        splits = [{"recipient_id": f"r{i}", "role": "affiliate", "percent": 10} for i in range(6)]

        response = _post(client, _make_payload(splits=splits), key="val-6-splits")

        assert response.status_code == 400

    def test_empty_splits_returns_400(self, client):
        response = _post(client, _make_payload(splits=[]), key="val-empty-splits")

        assert response.status_code == 400
