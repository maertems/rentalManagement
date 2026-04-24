from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.owner import Owner


async def get_current_user(
    accessToken: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Read JWT from the httpOnly `accessToken` cookie."""
    if not accessToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = decode_token(accessToken)
        if payload.get("type") != "access":
            raise JWTError("wrong token type")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the current user to be an admin."""
    if not current_user.isAdmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def get_withdraw_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require the current user to be an admin or a withdraw user."""
    if not current_user.isAdmin and not current_user.isWithdraw:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Withdraw privileges required",
        )
    return current_user


async def get_owner_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Owner | None:
    """
    Returns the Owner linked to the current user, or None if the user is admin.

    - Admin → None (no scope restriction, sees everything).
    - Non-admin with an owner → that Owner (restricts data to their scope).
    - Non-admin without an owner → 403 (orphan account, contact admin).
    """
    if current_user.isAdmin:
        return None
    if current_user.ownerId is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No owner profile linked to this account. Contact an administrator.",
        )
    owner = await db.get(Owner, current_user.ownerId)
    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner profile not found. Contact an administrator.",
        )
    return owner
