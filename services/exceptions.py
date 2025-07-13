from fastapi import HTTPException
from typing import Optional, List, Any

class APIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[List[dict]] = None,
        error_code: Optional[str] = None
    ):
        self.error_code = error_code
        self.details = details or []
        detail = {
            "error": error_code or "API Error",
            "message": message,
            "details": self.details,
            "status_code": status_code
        }
        super().__init__(status_code=status_code, detail=detail)

class ValidationError(APIError):
    def __init__(self, message: str, details: Optional[List[dict]] = None):
        super().__init__(
            status_code=422,
            message=message,
            details=details,
            error_code="VALIDATION_ERROR"
        )

class NotFoundError(APIError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            status_code=404,
            message=message,
            error_code="NOT_FOUND"
        )

class ServiceUnavailableError(APIError):
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=503,
            message=message,
            error_code="SERVICE_UNAVAILABLE"
        )

class InvalidImageError(APIError):
    def __init__(self, message: str = "Invalid image file"):
        super().__init__(
            status_code=400,
            message=message,
            error_code="INVALID_IMAGE"
        )