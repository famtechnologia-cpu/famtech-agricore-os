from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.all_models import Worker, WorkerPresence, FarmUser
from ..schemas.schemas import MaintenanceOut
from datetime import datetime, timezone
import json

router = APIRouter(prefix="/farms/{farm_id}/workers", tags=["workers"])

@router.get("")
async def list_workers(farm_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    result = await db.execute(select(Worker).where(Worker.farm_id == farm_id))
    workers = result.scalars().all()
    out = []
    for w in workers:
        # Get latest presence record
        pres = (await db.execute(
            select(WorkerPresence).where(WorkerPresence.worker_id == w.id)
            .order_by(WorkerPresence.entered_at.desc()).limit(1)
        )).scalar_one_or_none()
        out.append({
            "id": w.id, "name": w.name, "role": w.role, "active": w.active,
            "tag_device_id": w.tag_device_id,
            "last_seen_at": pres.entered_at.isoformat() if pres else None,
            "current_sector_id": pres.sector_id if pres and not pres.exited_at else None,
            "lat": pres.lat if pres else None,
            "lng": pres.lng if pres else None,
            "on_site": pres is not None and pres.exited_at is None,
        })
    return out

@router.get("/presence")
async def worker_presence(farm_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    result = await db.execute(
        select(WorkerPresence, Worker)
        .join(Worker, Worker.id == WorkerPresence.worker_id)
        .where(Worker.farm_id == farm_id, WorkerPresence.exited_at.is_(None))
        .order_by(WorkerPresence.entered_at.desc())
    )
    rows = result.all()
    return [
        {
            "worker_id": w.id, "worker_name": w.name, "worker_role": w.role,
            "sector_id": p.sector_id, "lat": p.lat, "lng": p.lng,
            "entered_at": p.entered_at.isoformat(),
        }
        for p, w in rows
    ]

@router.post("")
async def create_worker(farm_id: str, name: str, role: str = "Field Worker",
                         tag_device_id: Optional[str] = None,
                         db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    w = Worker(farm_id=farm_id, name=name, role=role, tag_device_id=tag_device_id, active=True)
    db.add(w)
    await db.commit()
    await db.refresh(w)
    return {"id": w.id, "name": w.name, "role": w.role}

async def _assert_member(farm_id, user_id, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m:
        from fastapi import HTTPException
        raise HTTPException(403, "Not a member of this farm")
