from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..core.deps import get_current_user
from ..models.all_models import Rule, RuleExecution, FarmUser, FarmRole, AuditLog
from ..schemas.schemas import RuleCreate, RuleOut

router = APIRouter(prefix="/farms/{farm_id}/rules", tags=["rules"])

@router.get("", response_model=list[RuleOut])
async def list_rules(farm_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    result = await db.execute(select(Rule).where(Rule.farm_id == farm_id).order_by(Rule.created_at.desc()))
    return result.scalars().all()

@router.post("", response_model=RuleOut, status_code=201)
async def create_rule(farm_id: str, body: RuleCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_role(farm_id, user.id, [FarmRole.OWNER, FarmRole.MANAGER], db)
    rule = Rule(farm_id=farm_id, **body.model_dump())
    db.add(rule)
    db.add(AuditLog(farm_id=farm_id, user_id=user.id, entity_type="rule", action="create"))
    await db.commit()
    await db.refresh(rule)
    return rule

@router.patch("/{rule_id}", response_model=RuleOut)
async def update_rule(farm_id: str, rule_id: str, body: RuleCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_role(farm_id, user.id, [FarmRole.OWNER, FarmRole.MANAGER], db)
    rule = await _get_rule(rule_id, farm_id, db)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(rule, k, v)
    await db.commit()
    await db.refresh(rule)
    return rule

@router.post("/{rule_id}/toggle")
async def toggle_rule(farm_id: str, rule_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_role(farm_id, user.id, [FarmRole.OWNER, FarmRole.MANAGER], db)
    rule = await _get_rule(rule_id, farm_id, db)
    rule.enabled = not rule.enabled
    action = "enable" if rule.enabled else "disable"
    db.add(AuditLog(farm_id=farm_id, user_id=user.id, entity_type="rule", entity_id=rule_id, action=action))
    await db.commit()
    return {"enabled": rule.enabled}

@router.get("/{rule_id}/executions")
async def rule_history(farm_id: str, rule_id: str, limit: int = 20, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await _assert_member(farm_id, user.id, db)
    result = await db.execute(select(RuleExecution).where(RuleExecution.rule_id == rule_id).order_by(RuleExecution.triggered_at.desc()).limit(limit))
    return result.scalars().all()

async def _get_rule(rule_id, farm_id, db):
    rule = (await db.execute(select(Rule).where(Rule.id == rule_id, Rule.farm_id == farm_id))).scalar_one_or_none()
    if not rule:
        raise HTTPException(404, "Rule not found")
    return rule

async def _assert_member(farm_id, user_id, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "Not a member of this farm")

async def _assert_role(farm_id, user_id, roles, db):
    m = (await db.execute(select(FarmUser).where(FarmUser.farm_id == farm_id, FarmUser.user_id == user_id))).scalar_one_or_none()
    if not m or m.role not in roles:
        raise HTTPException(403, "Insufficient permissions")
