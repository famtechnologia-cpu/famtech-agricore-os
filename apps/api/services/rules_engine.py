from __future__ import annotations
"""
Rules engine — evaluates threshold-based rules on each telemetry ingest.
Called after sensor readings are saved.
"""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.all_models import Rule, RuleExecution, SensorReading, Alert, AlertSeverity, AlertStatus, RuleTriggerType

log = logging.getLogger("rules-engine")

OPERATORS = {
    "lt": lambda v, t: v < t,
    "lte": lambda v, t: v <= t,
    "gt": lambda v, t: v > t,
    "gte": lambda v, t: v >= t,
    "eq": lambda v, t: v == t,
}


async def evaluate_rules_for_device(device_id: str, farm_id: str, db: AsyncSession):
    """Called after telemetry ingest — checks all enabled THRESHOLD rules for this farm."""
    rules = (await db.execute(
        select(Rule).where(
            Rule.farm_id == farm_id,
            Rule.enabled == True,
            Rule.trigger_type == RuleTriggerType.THRESHOLD,
        )
    )).scalars().all()

    for rule in rules:
        cfg = rule.trigger_config
        # Only evaluate rules targeting this device (or any device if no device_id specified)
        if cfg.get("device_id") and cfg["device_id"] != device_id:
            continue
        await _evaluate_threshold_rule(rule, device_id, farm_id, db)


async def _evaluate_threshold_rule(rule: Rule, device_id: str, farm_id: str, db: AsyncSession):
    cfg = rule.trigger_config
    metric = cfg.get("metric")
    operator = cfg.get("operator", "lt")
    threshold = float(cfg.get("value", 0))
    consecutive = rule.condition_json.get("consecutive_readings", 1) if rule.condition_json else 1

    # Fetch last N readings for this metric
    readings = (await db.execute(
        select(SensorReading)
        .where(SensorReading.device_id == device_id, SensorReading.metric == metric)
        .order_by(SensorReading.recorded_at.desc())
        .limit(consecutive)
    )).scalars().all()

    if len(readings) < consecutive:
        return  # Not enough data yet

    op_fn = OPERATORS.get(operator)
    if not op_fn:
        return

    # All consecutive readings must breach the threshold
    if not all(op_fn(r.value, threshold) for r in readings):
        return

    # Check we haven't already fired this rule recently (dedup: 1h window)
    if rule.last_fired_at:
        delta = (datetime.now(timezone.utc) - rule.last_fired_at).total_seconds()
        if delta < 3600:
            log.debug(f"Rule {rule.name} already fired recently, skipping")
            return

    # Fire the rule — create alert
    action = rule.action_json
    alert_cfg = action.get("create_alert", {})
    severity_str = alert_cfg.get("severity", "MEDIUM").upper()
    severity = AlertSeverity[severity_str]

    alert = Alert(
        farm_id=farm_id,
        device_id=device_id,
        severity=severity,
        type="threshold_breach",
        title=alert_cfg.get("title", f"Rule: {rule.name}"),
        message=f"Rule '{rule.name}' fired: {metric} {operator} {threshold} for {consecutive} consecutive readings.",
        context_json={"rule_id": rule.id, "metric": metric, "threshold": threshold, "value": readings[0].value},
        status=AlertStatus.OPEN,
    )
    db.add(alert)

    execution = RuleExecution(
        rule_id=rule.id,
        result="SUCCESS",
        context_json={"device_id": device_id, "metric": metric, "value": readings[0].value},
    )
    db.add(execution)

    rule.last_fired_at = datetime.now(timezone.utc)
    await db.commit()
    log.info(f"Rule '{rule.name}' fired → Alert created (severity={severity_str})")
