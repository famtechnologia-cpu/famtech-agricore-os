from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.all_models import Alert, AlertStatus, FarmUser, AuditLog
from ..schemas.schemas import AlertOut
from datetime import datetime, timezone

router = APIRouter(prefix="/farms/{farm_id}/alerts", tags=["alerts"])

@router.get("", response_model=list[AlertOut])
async def list_alerts(farm_id: str, severity: Optional[str] = None, status: Optional[str] = None,
                      limit: int = 50, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    q = select(Alert).where(Alert.farm_id == farm_id).order_by(Alert.created_at.desc()).limit(limit)
    if severity:
        q = q.where(Alert.severity == severity)
    if status:
        q = q.where(Alert.status == status)
    return (await db.execute(q)).scalars().all()

@router.post("/{alert_id}/acknowledge")
async def acknowledge(farm_id: str, alert_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    alert = await _get_alert(alert_id, farm_id, db)
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by = user.id
    db.add(AuditLog(farm_id=farm_id, user_id=user.id, entity_type="alert", entity_id=alert_id, action="acknowledge"))
    await db.commit()
    return {"status": "acknowledged"}

@router.post("/{alert_id}/resolve")
async def resolve(farm_id: str, alert_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    alert = await _get_alert(alert_id, farm_id, db)
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.now(timezone.utc)
    db.add(AuditLog(farm_id=farm_id, user_id=user.id, entity_type="alert", entity_id=alert_id, action="resolve"))
    await db.commit()
    return {"status": "resolved"}

async def _get_alert(alert_id, farm_id, db):
    alert = (await db.execute(select(Alert).where(Alert.id == alert_id, Alert.farm_id == farm_id))).scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    return alert

async def _assert_member(farm_id, user_id, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "Not a member of this farm")
