from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from fastapi import APIRouter, Depends

from app.database import get_db
from app.models.service import Service, ServiceStatus
from app.models.vehicle import Vehicle
from app.schemas.service import ServiceCreate, ServiceResponse, ServiceStatusUpdate, DashboardStats
from app.services.exceptions import ServiceNotFoundError
from app.services.workflow import validate_transition, check_booking_conflict
from app.services.priority import calculate_priority

router = APIRouter(prefix="/services", tags=["services"])


def _get_service_or_404(db: Session, service_id: int) -> Service:
    service = db.execute(
        select(Service)
        .options(joinedload(Service.vehicle))
        .where(Service.id == service_id)
    ).scalar_one_or_none()
    if service is None:
        raise ServiceNotFoundError(f"Service with id {service_id} not found")
    return service


@router.post("", response_model=ServiceResponse, status_code=201)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)):
    # Find or create the vehicle by registration number. We don't
    # duplicate vehicle info across services - each service just
    # references a vehicle_id.
    vehicle = db.execute(
        select(Vehicle).where(Vehicle.registration_number == payload.registration_number)
    ).scalar_one_or_none()

    if vehicle is None:
        vehicle = Vehicle(
            registration_number=payload.registration_number,
            owner_name=payload.owner_name,
            contact_number=payload.contact_number,
            vehicle_model=payload.vehicle_model,
        )
        db.add(vehicle)
        db.flush()  # assign vehicle.id without committing yet
    else:
        # Keep the vehicle's contact/owner info up to date with the
        # latest booking, in case the customer's details changed.
        vehicle.owner_name = payload.owner_name
        vehicle.contact_number = payload.contact_number
        vehicle.vehicle_model = payload.vehicle_model

    check_booking_conflict(db, vehicle.id, payload.appointment_date)

    service = Service(
        vehicle_id=vehicle.id,
        service_type=payload.service_type,
        issue_description=payload.issue_description,
        appointment_date=payload.appointment_date,
        status=ServiceStatus.BOOKED,
        priority=calculate_priority(payload.issue_description),
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get("", response_model=list[ServiceResponse])
def list_services(db: Session = Depends(get_db)):
    return db.execute(
        select(Service).options(joinedload(Service.vehicle)).order_by(Service.created_at.desc())
    ).scalars().all()


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db)):
    return _get_service_or_404(db, service_id)


@router.patch("/{service_id}/status", response_model=ServiceResponse)
def update_service_status(
    service_id: int, payload: ServiceStatusUpdate, db: Session = Depends(get_db)
):
    service = _get_service_or_404(db, service_id)
    validate_transition(service.status, payload.status)
    service.status = payload.status
    db.commit()
    db.refresh(service)
    return service


@router.get("/stats/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    services = db.execute(select(Service)).scalars().all()
    counts = {status: 0 for status in ServiceStatus}
    for s in services:
        counts[s.status] += 1
    return DashboardStats(
        total_services=len(services),
        booked=counts[ServiceStatus.BOOKED],
        inspection=counts[ServiceStatus.INSPECTION],
        repair=counts[ServiceStatus.REPAIR],
        completed=counts[ServiceStatus.COMPLETED],
        cancelled=counts[ServiceStatus.CANCELLED],
    )
