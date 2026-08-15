from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Structured error body returned for all handled API errors."""

    error: str
    message: str
    details: dict | None = None
