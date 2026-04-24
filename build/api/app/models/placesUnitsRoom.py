from datetime import datetime
from sqlalchemy import BigInteger, String, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class PlacesUnitsRoom(Base):
    __tablename__ = "placesUnitsRooms"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    surfaceArea: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    placesUnitsId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
