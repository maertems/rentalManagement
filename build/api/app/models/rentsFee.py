from datetime import datetime
from sqlalchemy import BigInteger, String, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RentsFee(Base):
    __tablename__ = "rentsFees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenantId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    applicationMonth: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subDescription: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
