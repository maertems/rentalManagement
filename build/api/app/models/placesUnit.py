from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, SmallInteger, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class PlacesUnit(Base):
    __tablename__ = "placesUnits"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    flatshare: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    zipCode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    surfaceArea: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    placeId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    friendlyName: Mapped[str | None] = mapped_column(String(255), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
