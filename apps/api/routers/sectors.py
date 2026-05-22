from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.all_models import Sector, SectorType, FarmUser
from ..schemas.schemas import SectorCreate, SectorOut
from fastapi import HTTPException

router = APIRouter(prefix="/farms/{farm_id}/sectors", tags=["sectors"])

@router.get("", response_model=list[SectorOut])
async def list_sectors(farm_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    result = await db.execute(select(Sector).where(Sector.farm_id == farm_id))
    return result.scalars().all()

@router.post("", response_model=SectorOut, status_code=201)
async def create_sector(farm_id: str, body: SectorCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    sector = Sector(farm_id=farm_id, **body.model_dump(exclude_none=True))
    db.add(sector)
    await db.commit()
    await db.refresh(sector)
    return sector

@router.patch("/{sector_id}", response_model=SectorOut)
async def update_sector(farm_id: str, sector_id: str, body: SectorCreate,
                         db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    sector = (await db.execute(select(Sector).where(Sector.id == sector_id, Sector.farm_id == farm_id))).scalar_one_or_none()
    if not sector:
        raise HTTPException(404, "Sector not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(sector, k, v)
    await db.commit()
    await db.refresh(sector)
    return sector

@router.delete("/{sector_id}", status_code=204)
async def delete_sector(farm_id: str, sector_id: str,
                         db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    sector = (await db.execute(select(Sector).where(Sector.id == sector_id, Sector.farm_id == farm_id))).scalar_one_or_none()
    if not sector:
        raise HTTPException(404, "Sector not found")
    await db.delete(sector)
    await db.commit()

async def _assert_member(farm_id, user_id, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "Not a member of this farm")
