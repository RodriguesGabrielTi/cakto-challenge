from rest_framework import serializers

from src.billing.models import PaymentMethod


class SplitSerializer(serializers.Serializer):
    recipient_id = serializers.CharField(max_length=255)
    role = serializers.CharField(max_length=50)
    percent = serializers.DecimalField(max_digits=5, decimal_places=2)


class PaymentInputSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    payment_method = serializers.ChoiceField(choices=PaymentMethod)
    installments = serializers.IntegerField(default=1)
    splits = SplitSerializer(many=True)


class ReceivableSerializer(serializers.Serializer):
    recipient_id = serializers.CharField()
    role = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class OutboxEventSerializer(serializers.Serializer):
    type = serializers.CharField()
    status = serializers.CharField()


class PaymentOutputSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    status = serializers.CharField()
    gross_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    platform_fee_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    receivables = ReceivableSerializer(many=True)
    outbox_event = OutboxEventSerializer()
