from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import get_db
from .security import decode_token
from ..models.all_models import User, FarmUser, FarmRole

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user

async def require_farm_role(
    farm_id: str,
    allowed_roles: list[FarmRole],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FarmUser:
    if current_user.is_superuser:
        return  # superusers bypass role checks
    result = await db.execute(
        select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()
    if not membership or membership.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return membership

def require_roles(*roles: FarmRole):
    """Factory: returns a dependency that checks farm membership and role."""
    async def _check(
        farm_id: str,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        return await require_farm_role(farm_id, list(roles), user, db)
    return _check
