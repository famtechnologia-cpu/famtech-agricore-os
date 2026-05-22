from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.all_models import MaintenanceEvent, Device, FarmUser, FarmRole
from ..schemas.schemas import MaintenanceCreate, MaintenanceOut

router = APIRouter(prefix="/farms/{farm_id}/maintenance", tags=["maintenance"])

@router.get("", response_model=list[MaintenanceOut])
async def list_maintenance(farm_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    result = await db.execute(
        select(MaintenanceEvent).where(MaintenanceEvent.farm_id == farm_id).order_by(MaintenanceEvent.performed_at.desc())
    )
    return result.scalars().all()

@router.post("", response_model=MaintenanceOut, status_code=201)
async def log_maintenance(farm_id: str, body: MaintenanceCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_role(farm_id, user.id, [FarmRole.OWNER, FarmRole.MANAGER, FarmRole.TECHNICIAN], db)
    # Verify device belongs to farm
    device = (await db.execute(select(Device).where(Device.id == body.device_id, Device.farm_id == farm_id))).scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found in this farm")
    event = MaintenanceEvent(
        **body.model_dump(exclude_none=True),
        farm_id=farm_id,
        performed_by=user.id,
        performed_at=body.performed_at or datetime.now(timezone.utc),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event

@router.get("/device/{device_id}", response_model=list[MaintenanceOut])
async def device_maintenance(farm_id: str, device_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    result = await db.execute(
        select(MaintenanceEvent).where(MaintenanceEvent.device_id == device_id, MaintenanceEvent.farm_id == farm_id).order_by(MaintenanceEvent.performed_at.desc())
    )
    return result.scalars().all()

async def _assert_member(farm_id, user_id, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "Not a member of this farm")

async def _assert_role(farm_id, user_id, roles, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m or m.role not in roles:
        raise HTTPException(403, "Insufficient permissions")
