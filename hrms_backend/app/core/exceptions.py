from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "An error occurred",
        code: str = "app_error",
    ) -> None:
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, code="not_found")


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Unauthorized") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, code="unauthorized")


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, code="forbidden")


class ConflictError(AppException):
    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, code="conflict")


class ValidationError(AppException):
    def __init__(self, detail: str = "Validation failed") -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail, code="validation_error")
