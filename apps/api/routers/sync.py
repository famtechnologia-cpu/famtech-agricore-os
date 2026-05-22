from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..core.database import get_db
from ..models.all_models import SensorReading
from ..services.rules_engine import RulesEngine
import uuid
from datetime import datetime, timezone

log = logging.getLogger(__name__)
router = APIRouter(prefix="/sync", tags=["sync"])

class SyncPayload(BaseModel):
    entity_type: str
    operation: str
    payload: Dict[str, Any]

@router.post("/push", status_code=201)
async def sync_push(data: SyncPayload, db: AsyncSession = Depends(get_db)):
    """
    Accepts store-and-forward sync data from the Edge Gateway.
    Because the gateway operates in offline environments, this endpoint 
    must handle potentially delayed or bulk data.
    """
    if data.entity_type == "telemetry" and data.operation == "push":
        # Handle telemetry batch
        payload = data.payload
        device_id = payload.get("device_id")
        readings = payload.get("readings", [])
        
        if not device_id:
            raise HTTPException(status_code=400, detail="Missing device_id in telemetry payload")

        # In a real production setup, we would verify the edge gateway's token here.
        # For the MVP, we accept the sync payload.
        
        now = datetime.now(timezone.utc)
        
        try:
            for r in readings:
                recorded_at = r.get("recorded_at")
                if recorded_at:
                    try:
                        dt = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
                    except:
                        dt = now
                else:
                    dt = now
                    
                reading = SensorReading(
                    id=str(uuid.uuid4()),
                    device_id=device_id,
                    farm_id=payload.get("farm_id", "unknown_farm"),
                    metric=r["metric"],
                    value=float(r["value"]),
                    unit=r.get("unit"),
                    recorded_at=dt,
                    synced_at=now
                )
                db.add(reading)
                
            await db.commit()
            
            # Fire rules engine on the synced data
            # Note: in a high volume env, this should be sent to a background worker
            try:
                for r in readings:
                    await RulesEngine.evaluate_telemetry(
                        db, 
                        payload.get("farm_id", ""), 
                        device_id, 
                        r["metric"], 
                        float(r["value"])
                    )
            except Exception as e:
                log.error(f"Rule evaluation failed during sync: {e}")
                
            return {"status": "success", "processed": len(readings)}
            
        except Exception as e:
            await db.rollback()
            log.error(f"Sync insertion failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to process sync payload")
            
    else:
        # Extend here for other sync entities (alerts, etc.)
        log.warning(f"Unhandled sync entity/operation: {data.entity_type} / {data.operation}")
        return {"status": "ignored"}
