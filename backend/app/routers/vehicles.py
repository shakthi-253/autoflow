from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleResponse
from app.services.exceptions import VehicleNotFoundError

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleResponse, status_code=201)
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)):
    """
    Create a vehicle directly. Note: creating a service via POST /services
    will also create the vehicle if it doesn't exist yet (by registration
    number), so this endpoint is mainly useful for pre-registering vehicles.
    """
    existing = db.execute(
        select(Vehicle).where(Vehicle.registration_number == payload.registration_number)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("", response_model=list[VehicleResponse])
def list_vehicles(db: Session = Depends(get_db)):
    return db.execute(select(Vehicle).order_by(Vehicle.created_at.desc())).scalars().all()


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.get(Vehicle, vehicle_id)
    if vehicle is None:
        raise VehicleNotFoundError(f"Vehicle with id {vehicle_id} not found")
    return vehicle
