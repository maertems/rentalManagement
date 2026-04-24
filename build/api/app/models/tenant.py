from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, SmallInteger, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    genre: Mapped[str | None] = mapped_column(
        Enum("Mlle", "Mme", "M", "Societe"), nullable=True
    )
    firstName: Mapped[str | None] = mapped_column(String(150), nullable=True)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    billingSameAsRental: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    billingAddress: Mapped[str | None] = mapped_column(String(500), nullable=True)
    billingZipCode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    billingCity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    billingPhone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    withdrawName: Mapped[str | None] = mapped_column(String(255), nullable=True)
    withdrawDay: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    placeUnitId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    placeUnitRoomId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sendNoticeOfLeaseRental: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    sendLeaseRental: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    active: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    dateEntrance: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dateExit: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    warantyReceiptId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
