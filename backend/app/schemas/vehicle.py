import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

# Alphanumeric with optional spaces/hyphens, e.g. "TN09AB1234" or "TN-09-AB-1234"
REGISTRATION_NUMBER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\- ]{3,15}[A-Za-z0-9]$")
# Accepts numbers with optional leading + and 7-15 digits total
CONTACT_NUMBER_PATTERN = re.compile(r"^\+?\d{7,15}$")


class VehicleBase(BaseModel):
    registration_number: str
    owner_name: str
    contact_number: str
    vehicle_model: str

    @field_validator("registration_number")
    @classmethod
    def validate_registration_number(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Registration number is required")
        if len(v) > 20:
            raise ValueError("Registration number must be at most 20 characters")
        if not REGISTRATION_NUMBER_PATTERN.match(v):
            raise ValueError(
                "Registration number must be 5-17 alphanumeric characters "
                "(spaces/hyphens allowed), e.g. TN09AB1234"
            )
        return v

    @field_validator("owner_name")
    @classmethod
    def validate_owner_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Owner name is required")
        if len(v) > 100:
            raise ValueError("Owner name must be at most 100 characters")
        return v

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Contact number is required")
        if not CONTACT_NUMBER_PATTERN.match(v):
            raise ValueError(
                "Contact number must be 7-15 digits, optionally starting with +"
            )
        return v

    @field_validator("vehicle_model")
    @classmethod
    def validate_vehicle_model(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Vehicle model is required")
        if len(v) > 100:
            raise ValueError("Vehicle model must be at most 100 characters")
        return v


class VehicleCreate(VehicleBase):
    pass


class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
