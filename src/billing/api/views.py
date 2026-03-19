from injector import inject
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from src.billing.api.serializers import PaymentInputSerializer, PaymentOutputSerializer
from src.billing.services.payment_service import PaymentService


class PaymentView(APIView):
    _payment_service: PaymentService

    @inject
    def setup(self, request, *args, payment_service: PaymentService, **kwargs):
        super().setup(request, *args, **kwargs)
        self._payment_service = payment_service

    def post(self, request: Request) -> Response:
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response(
                {"detail": "Header Idempotency-Key é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        input_serializer = PaymentInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        result = self._payment_service.process(input_serializer.validated_data, idempotency_key)

        output_serializer = PaymentOutputSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
