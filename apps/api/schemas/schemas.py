from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, ConfigDict

# ── BASE ──────────────────────────────────────────────────────────────────────
class TimestampMixin(BaseModel):
    created_at: datetime

# ── AUTH ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime

# ── FARM ──────────────────────────────────────────────────────────────────────
class FarmCreate(BaseModel):
    name: str
    timezone: str = "UTC"
    lat: Optional[float] = None
    lng: Optional[float] = None
    boundary_geojson: Optional[dict] = None

class FarmOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    timezone: str
    lat: Optional[float]
    lng: Optional[float]
    boundary_geojson: Optional[dict]
    created_at: datetime

class FarmSummary(BaseModel):
    """Dashboard snapshot — loaded in < 1 request"""
    farm: FarmOut
    device_count: int
    online_devices: int
    open_alerts: int
    critical_alerts: int
    workers_on_site: int
    last_updated: datetime

# ── SECTOR ────────────────────────────────────────────────────────────────────
class SectorCreate(BaseModel):
    name: str
    type: str = "FIELD"
    boundary_geojson: Optional[dict] = None
    parent_id: Optional[str] = None

class SectorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    farm_id: str
    name: str
    type: str
    boundary_geojson: Optional[dict]
    parent_id: Optional[str]
    created_at: datetime

# ── DEVICE ────────────────────────────────────────────────────────────────────
class DeviceRegister(BaseModel):
    name: str
    type: str
    serial: Optional[str] = None
    sector_id: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    farm_id: str
    sector_id: Optional[str]
    name: str
    type: str
    serial: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    status: str
    battery_pct: Optional[float]
    firmware_ver: Optional[str]
    last_seen_at: Optional[datetime]
    registered_at: datetime

class DeviceRegisterResponse(DeviceOut):
    api_key: str  # Only returned once at registration

# ── TELEMETRY ─────────────────────────────────────────────────────────────────
class TelemetryPayload(BaseModel):
    readings: List[Dict[str, Any]]  # [{metric, value, unit, recorded_at}]
    device_id: str
    firmware_ver: Optional[str] = None
    battery_pct: Optional[float] = None

class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    device_id: str
    metric: str
    value: float
    unit: Optional[str]
    recorded_at: datetime

# ── ALERT ─────────────────────────────────────────────────────────────────────
class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    farm_id: str
    device_id: Optional[str]
    sector_id: Optional[str]
    severity: str
    type: str
    title: str
    message: str
    context_json: Optional[dict]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]

# ── RULE ──────────────────────────────────────────────────────────────────────
class RuleCreate(BaseModel):
    name: str
    trigger_type: str
    trigger_config: dict
    condition_json: Optional[dict] = None
    action_json: dict

class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    farm_id: str
    name: str
    enabled: bool
    trigger_type: str
    trigger_config: dict
    condition_json: Optional[dict]
    action_json: dict
    last_fired_at: Optional[datetime]
    created_at: datetime

# ── MAINTENANCE ───────────────────────────────────────────────────────────────
class MaintenanceCreate(BaseModel):
    device_id: str
    type: str
    description: str
    performed_at: Optional[datetime] = None
    next_due_at: Optional[datetime] = None
    cost: Optional[float] = None
    notes: Optional[str] = None

class MaintenanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    device_id: str
    farm_id: str
    type: str
    description: str
    performed_by: Optional[str]
    performed_at: datetime
    next_due_at: Optional[datetime]
    cost: Optional[float]
    notes: Optional[str]
