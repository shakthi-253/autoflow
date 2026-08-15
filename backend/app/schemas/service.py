from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.service import ServiceType, ServiceStatus, ServicePriority
from app.schemas.vehicle import VehicleBase, VehicleResponse

MAX_ISSUE_DESCRIPTION_LENGTH = 1000


class ServiceCreate(VehicleBase):
    """
    Payload for creating a service. Combines vehicle info (used to find
    or create the Vehicle record) with the service-specific fields.
    """

    service_type: ServiceType
    issue_description: str
    appointment_date: datetime

    @field_validator("issue_description")
    @classmethod
    def validate_issue_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Issue description is required")
        if len(v) > MAX_ISSUE_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Issue description must be at most {MAX_ISSUE_DESCRIPTION_LENGTH} characters"
            )
        return v

    @model_validator(mode="after")
    def validate_appointment_date(self):
        # Reasonable bounds: not absurdly far in the past, not more than
        # 2 years out. Keeps the "valid date" requirement meaningful
        # without being overly strict about timezones.
        min_date = datetime(2000, 1, 1)
        max_date = datetime(datetime.now().year + 2, 12, 31)
        if self.appointment_date < min_date or self.appointment_date > max_date:
            raise ValueError("Appointment date is out of a reasonable range")
        return self


class ServiceStatusUpdate(BaseModel):
    status: ServiceStatus


class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    service_type: ServiceType
    issue_description: str
    appointment_date: datetime
    status: ServiceStatus
    priority: ServicePriority
    created_at: datetime
    updated_at: datetime
    vehicle: VehicleResponse


class DashboardStats(BaseModel):
    total_services: int
    booked: int
    inspection: int
    repair: int
    completed: int
    cancelled: int
