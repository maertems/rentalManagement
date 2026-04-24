from datetime import datetime
from sqlalchemy import BigInteger, SmallInteger, Numeric, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Rent(Base):
    __tablename__ = "rents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenantId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    type: Mapped[str | None] = mapped_column(
        Enum("Loyer", "Charges", "Garantie"), nullable=True
    )
    price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    dateExpiration: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    active: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
