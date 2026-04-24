from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from app.crud.user import crud_user
from app.schemas.auth import LoginInput
from app.schemas.user import UserRead
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


def _set_auth_cookies(response: Response, user_id: int) -> None:
    """Attach accessToken + refreshToken as httpOnly cookies."""
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(
        key="accessToken",
        value=access_token,
        max_age=settings.JWT_EXPIRES_MIN * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        max_age=settings.JWT_REFRESH_EXPIRES_DAYS * 86400,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="accessToken", path="/", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie(key="refreshToken", path="/", domain=settings.COOKIE_DOMAIN)


@router.post("/login", response_model=UserRead)
async def login(
    payload: LoginInput,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await crud_user.get_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.passwordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    _set_auth_cookies(response, user.id)
    return user


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(
    response: Response,
    refreshToken: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refreshToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )
    try:
        data = decode_token(refreshToken)
        if data.get("type") != "refresh":
            raise JWTError("wrong token type")
        user_id = int(data["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    _set_auth_cookies(response, user.id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    _clear_auth_cookies(response)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
