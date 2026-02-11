class DomainException(Exception):
    def __init__(self, message: str = "Erro de domínio."):
        self.message = message
        super().__init__(self.message)


class BusinessValidationError(DomainException):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__("Erro de validação de negócio.")


class ConflictError(DomainException):
    def __init__(self, message: str = "Conflito com recurso existente."):
        super().__init__(message)
