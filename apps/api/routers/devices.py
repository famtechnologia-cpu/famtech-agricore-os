from __future__ import annotations
from typing import Optional
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.deps import get_current_user
from ..core.security import hash_password, verify_password
from ..models.all_models import Device, DeviceStatus, SensorReading, FarmUser, FarmRole
from ..schemas.schemas import DeviceRegister, DeviceOut, DeviceRegisterResponse, TelemetryPayload, ReadingOut

router = APIRouter(prefix="/farms/{farm_id}/devices", tags=["devices"])

@router.get("", response_model=list[DeviceOut])
async def list_devices(farm_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    result = await db.execute(select(Device).where(Device.farm_id == farm_id))
    return result.scalars().all()

@router.post("/register", response_model=DeviceRegisterResponse, status_code=201)
async def register_device(farm_id: str, body: DeviceRegister, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_role(farm_id, user.id, [FarmRole.OWNER, FarmRole.MANAGER, FarmRole.TECHNICIAN], db)
    api_key = secrets.token_urlsafe(32)
    device = Device(
        farm_id=farm_id,
        name=body.name,
        type=body.type,
        serial=body.serial,
        sector_id=body.sector_id,
        lat=body.lat,
        lng=body.lng,
        status=DeviceStatus.OFFLINE,
        api_key_hash=hash_password(api_key),
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return DeviceRegisterResponse(
        id=device.id, farm_id=device.farm_id, sector_id=device.sector_id,
        name=device.name, type=device.type, serial=device.serial,
        lat=device.lat, lng=device.lng, status=device.status.value,
        battery_pct=device.battery_pct, firmware_ver=device.firmware_ver,
        last_seen_at=device.last_seen_at, registered_at=device.registered_at,
        api_key=api_key,
    )

@router.get("/{device_id}", response_model=DeviceOut)
async def get_device(farm_id: str, device_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    return await _get_device_or_404(device_id, farm_id, db)

@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(farm_id: str, device_id: str, body: DeviceRegister, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_role(farm_id, user.id, [FarmRole.OWNER, FarmRole.MANAGER, FarmRole.TECHNICIAN], db)
    device = await _get_device_or_404(device_id, farm_id, db)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(device, k, v)
    await db.commit()
    await db.refresh(device)
    return device

@router.get("/{device_id}/readings", response_model=list[ReadingOut])
async def device_readings(farm_id: str, device_id: str, metric: Optional[str] = None,
                          limit: int = 100, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    q = select(SensorReading).where(SensorReading.device_id == device_id).order_by(SensorReading.recorded_at.desc()).limit(limit)
    if metric:
        q = q.where(SensorReading.metric == metric)
    result = await db.execute(q)
    return result.scalars().all()

# ── Device telemetry push (API key auth) ─────────────────────────────────────
telemetry_router = APIRouter(prefix="/devices", tags=["telemetry"])

@telemetry_router.post("/telemetry")
async def ingest_telemetry(
    body: TelemetryPayload,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    # Authorization: ApiKey <key>
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "ApiKey":
        raise HTTPException(401, "Invalid authorization format")
    api_key = parts[1]
    device = (await db.execute(select(Device).where(Device.id == body.device_id))).scalar_one_or_none()
    if not device or not device.api_key_hash or not verify_password(api_key, device.api_key_hash):
        raise HTTPException(401, "Device authentication failed")

    now = datetime.now(timezone.utc)
    readings = []
    for r in body.readings:
        readings.append(SensorReading(
            device_id=device.id,
            farm_id=device.farm_id,
            metric=r["metric"],
            value=float(r["value"]),
            unit=r.get("unit"),
            quality=r.get("quality"),
            recorded_at=r.get("recorded_at", now),
        ))
    db.add_all(readings)
    device.last_seen_at = now
    device.status = DeviceStatus.ONLINE
    if body.battery_pct is not None:
        device.battery_pct = body.battery_pct
    if body.firmware_ver:
        device.firmware_ver = body.firmware_ver
    await db.commit()
    return {"accepted": len(readings)}

# ── helpers ───────────────────────────────────────────────────────────────────
async def _get_device_or_404(device_id: str, farm_id: str, db):
    d = (await db.execute(select(Device).where(Device.id == device_id, Device.farm_id == farm_id))).scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Device not found")
    return d

async def _assert_member(farm_id: str, user_id: str, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "Not a member of this farm")

async def _assert_role(farm_id: str, user_id: str, roles: list, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m or m.role not in roles:
        raise HTTPException(403, "Insufficient permissions")
