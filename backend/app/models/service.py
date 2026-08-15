import enum
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ServiceType(str, enum.Enum):
    GENERAL_SERVICE = "GENERAL_SERVICE"
    OIL_CHANGE = "OIL_CHANGE"
    BRAKE_SERVICE = "BRAKE_SERVICE"
    ENGINE_REPAIR = "ENGINE_REPAIR"
    TYRE_SERVICE = "TYRE_SERVICE"


class ServiceStatus(str, enum.Enum):
    BOOKED = "BOOKED"
    INSPECTION = "INSPECTION"
    REPAIR = "REPAIR"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ServicePriority(str, enum.Enum):
    """
    Derived from the issue description at creation time - see
    app/services/priority.py::calculate_priority. Never accepted as
    direct user input (ServiceCreate has no priority field).
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# Active statuses are the ones that occupy a vehicle's appointment slot
# and therefore participate in the booking-conflict rule.
ACTIVE_STATUSES = {ServiceStatus.BOOKED, ServiceStatus.INSPECTION, ServiceStatus.REPAIR}

# The single source of truth for allowed workflow transitions. Enforced
# in app/services/workflow.py regardless of what the frontend shows.
ALLOWED_TRANSITIONS: dict[ServiceStatus, set[ServiceStatus]] = {
    ServiceStatus.BOOKED: {ServiceStatus.INSPECTION, ServiceStatus.CANCELLED},
    ServiceStatus.INSPECTION: {ServiceStatus.REPAIR, ServiceStatus.CANCELLED},
    ServiceStatus.REPAIR: {ServiceStatus.COMPLETED},
    ServiceStatus.COMPLETED: set(),
    ServiceStatus.CANCELLED: set(),
}


class Service(Base):
    """
    A single service job for a vehicle, moving through the
    BOOKED -> INSPECTION -> REPAIR -> COMPLETED workflow (or CANCELLED
    from BOOKED/INSPECTION).
    """

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_type: Mapped[ServiceType] = mapped_column(
        SAEnum(ServiceType), nullable=False
    )
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    appointment_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[ServiceStatus] = mapped_column(
        SAEnum(ServiceStatus), nullable=False, default=ServiceStatus.BOOKED
    )
    priority: Mapped[ServicePriority] = mapped_column(
        SAEnum(ServicePriority), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    vehicle = relationship("Vehicle", back_populates="services")
