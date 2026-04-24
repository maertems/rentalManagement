from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings


def hash_password(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()


def verify_password(p: str, h: str) -> bool:
    return bcrypt.checkpw(p.encode(), h.encode())


def create_access_token(sub: int, expires: timedelta | None = None) -> str:
    exp = datetime.now(timezone.utc) + (
        expires or timedelta(minutes=settings.JWT_EXPIRES_MIN)
    )
    payload = {"sub": str(sub), "exp": exp, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_refresh_token(sub: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_EXPIRES_DAYS
    )
    payload = {"sub": str(sub), "exp": exp, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
