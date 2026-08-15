class AppError(Exception):
    """Base class for application errors that map to structured HTTP responses."""

    status_code = 400
    error_code = "APP_ERROR"

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"


class VehicleNotFoundError(NotFoundError):
    error_code = "VEHICLE_NOT_FOUND"


class ServiceNotFoundError(NotFoundError):
    error_code = "SERVICE_NOT_FOUND"


class InvalidTransitionError(AppError):
    status_code = 409
    error_code = "INVALID_TRANSITION"


class BookingConflictError(AppError):
    status_code = 409
    error_code = "BOOKING_CONFLICT"


class ValidationAppError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
