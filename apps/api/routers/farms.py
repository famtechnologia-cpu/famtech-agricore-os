from __future__ import annotations
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.all_models import Farm, FarmUser, FarmRole, Device, Alert, AlertStatus, Worker, DeviceStatus
from ..schemas.schemas import FarmCreate, FarmOut, FarmSummary

router = APIRouter(prefix="/farms", tags=["farms"])

@router.post("", response_model=FarmOut, status_code=201)
async def create_farm(body: FarmCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    farm = Farm(**body.model_dump())
    db.add(farm)
    await db.flush()
    membership = FarmUser(farm_id=farm.id, user_id=user.id, role=FarmRole.OWNER)
    db.add(membership)
    await db.commit()
    await db.refresh(farm)
    return farm

@router.get("", response_model=list[FarmOut])
async def list_farms(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if user.is_superuser:
        result = await db.execute(select(Farm).where(Farm.is_active == True))
        return result.scalars().all()
    result = await db.execute(
        select(Farm).join(FarmUser, FarmUser.farm_id == Farm.id)
        .where(FarmUser.user_id == user.id, Farm.is_active == True)
    )
    return result.scalars().all()

@router.get("/{farm_id}", response_model=FarmOut)
async def get_farm(farm_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    farm = await _get_farm_or_404(farm_id, db)
    await _assert_member(farm_id, user.id, db)
    return farm

@router.patch("/{farm_id}", response_model=FarmOut)
async def update_farm(farm_id: str, body: FarmCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    farm = await _get_farm_or_404(farm_id, db)
    await _assert_role(farm_id, user.id, [FarmRole.OWNER, FarmRole.MANAGER], db)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(farm, k, v)
    await db.commit()
    await db.refresh(farm)
    return farm

@router.get("/{farm_id}/summary", response_model=FarmSummary)
async def farm_summary(farm_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    farm = await _get_farm_or_404(farm_id, db)
    await _assert_member(farm_id, user.id, db)
    device_count = (await db.execute(select(func.count()).select_from(Device).where(Device.farm_id == farm_id))).scalar()
    online_devices = (await db.execute(select(func.count()).select_from(Device).where(Device.farm_id == farm_id, Device.status == DeviceStatus.ONLINE))).scalar()
    open_alerts = (await db.execute(select(func.count()).select_from(Alert).where(Alert.farm_id == farm_id, Alert.status == AlertStatus.OPEN))).scalar()
    from ..models.all_models import AlertSeverity
    critical_alerts = (await db.execute(select(func.count()).select_from(Alert).where(Alert.farm_id == farm_id, Alert.status == AlertStatus.OPEN, Alert.severity == AlertSeverity.CRITICAL))).scalar()
    workers_on_site = (await db.execute(select(func.count()).select_from(Worker).where(Worker.farm_id == farm_id, Worker.active == True))).scalar()
    return FarmSummary(
        farm=FarmOut.model_validate(farm),
        device_count=device_count, online_devices=online_devices,
        open_alerts=open_alerts, critical_alerts=critical_alerts,
        workers_on_site=workers_on_site, last_updated=datetime.now(timezone.utc),
    )

@router.post("/{farm_id}/invite")
async def invite_user(farm_id: str, email: str, role: FarmRole = FarmRole.OPERATOR, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_role(farm_id, user.id, [FarmRole.OWNER, FarmRole.MANAGER], db)
    from ..models.all_models import User as UserModel
    target = (await db.execute(select(UserModel).where(UserModel.email == email))).scalar_one_or_none()
    if not target:
        raise HTTPException(404, "User not found")
    existing = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == target.id))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "User already a member")
    db.add(FarmUser(farm_id=farm_id, user_id=target.id, role=role))
    await db.commit()
    return {"status": "invited"}

# ── helpers ───────────────────────────────────────────────────────────────────
async def _get_farm_or_404(farm_id: str, db):
    farm = (await db.execute(select(Farm).where(Farm.id == farm_id))).scalar_one_or_none()
    if not farm:
        raise HTTPException(404, "Farm not found")
    return farm

async def _assert_member(farm_id: str, user_id: str, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "Not a member of this farm")

async def _assert_role(farm_id: str, user_id: str, roles: list, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m or m.role not in roles:
        raise HTTPException(403, "Insufficient permissions")
