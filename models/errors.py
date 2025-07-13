from pydantic import BaseModel
from typing import Optional, List, Any

class ErrorDetail(BaseModel):
    field: Optional[str] = None
    message: str
    code: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    status_code: int

class ValidationErrorResponse(BaseModel):
    error: str = "Validation Error"
    message: str
    details: List[ErrorDetail]
    status_code: int = 422