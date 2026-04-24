from datetime import datetime
from sqlalchemy import BigInteger, String, SmallInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(String(150), nullable=True, unique=True)
    passwordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    tokenKey: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verified: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    emailVisibility: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    isAdmin: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    isWithdraw: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ownerId: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    lastResetSentAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lastVerificationSentAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
