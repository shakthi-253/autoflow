from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vehicle(Base):
    """
    A vehicle owned by a customer. A vehicle is uniquely identified by
    its registration number and can have many services over time.
    """

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    registration_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    owner_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_model: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    services = relationship(
        "Service", back_populates="vehicle", cascade="all, delete-orphan"
    )
