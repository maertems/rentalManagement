from datetime import datetime
from sqlalchemy import BigInteger, SmallInteger, Numeric, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RentReceipt(Base):
    __tablename__ = "rentReceipts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    placeUnitId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    placeUnitRoomId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenantId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    periodBegin: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    periodEnd: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    paid: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    pdfFilename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
