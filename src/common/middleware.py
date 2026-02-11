from django.http import JsonResponse

from src.common.exceptions import BusinessValidationError, ConflictError, DomainException

DOMAIN_STATUS_MAP = {
    BusinessValidationError: 400,
    ConflictError: 409,
}

DEFAULT_DOMAIN_STATUS = 400


class DomainExceptionMiddleware:
    """Traduz exceções de domínio para respostas HTTP."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, DomainException):
            return None

        status_code = DOMAIN_STATUS_MAP.get(type(exception), DEFAULT_DOMAIN_STATUS)

        if isinstance(exception, BusinessValidationError):
            return JsonResponse(exception.errors, status=status_code)

        return JsonResponse({"detail": exception.message}, status=status_code)
