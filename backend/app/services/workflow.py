"""
Core business rules for AutoFlow, independent of the HTTP layer.

This is the single source of truth for:
- valid status transitions
- the booking-conflict rule

Routers call into this module rather than encoding rules themselves,
so the same checks apply no matter how the API is called.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service import Service, ServiceStatus, ALLOWED_TRANSITIONS, ACTIVE_STATUSES
from app.services.exceptions import InvalidTransitionError, BookingConflictError


def is_transition_allowed(current: ServiceStatus, target: ServiceStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def validate_transition(current: ServiceStatus, target: ServiceStatus) -> None:
    """Raise InvalidTransitionError if the transition is not allowed."""
    if not is_transition_allowed(current, target):
        raise InvalidTransitionError(
            f"Cannot change status from {current.value} to {target.value}",
            details={"current_status": current.value, "requested_status": target.value},
        )


def check_booking_conflict(
    db: Session,
    vehicle_id: int,
    appointment_date,
    exclude_service_id: int | None = None,
) -> None:
    """
    A vehicle cannot have another active (BOOKED/INSPECTION/REPAIR) service
    for the same appointment date/time. Raises BookingConflictError if a
    conflict exists.
    """
    query = select(Service).where(
        Service.vehicle_id == vehicle_id,
        Service.appointment_date == appointment_date,
        Service.status.in_(ACTIVE_STATUSES),
    )
    if exclude_service_id is not None:
        query = query.where(Service.id != exclude_service_id)

    conflicting = db.execute(query).scalars().first()
    if conflicting is not None:
        raise BookingConflictError(
            "This vehicle already has an active booking for the same appointment date/time",
            details={
                "conflicting_service_id": conflicting.id,
                "appointment_date": str(appointment_date),
            },
        )
