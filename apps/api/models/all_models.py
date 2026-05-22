from __future__ import annotations
import uuid
import enum
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Float, Integer, ForeignKey, Text, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
try:
    from core.base import Base          # standalone: alembic, scripts
except ImportError:
    from ..core.base import Base        # as package: uvicorn

def utcnow():
    return datetime.now(timezone.utc)

def new_id():
    return str(uuid.uuid4())

# ── ENUMS ─────────────────────────────────────────────────────────────────────

class FarmRole(str, enum.Enum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    OPERATOR = "OPERATOR"
    TECHNICIAN = "TECHNICIAN"
    SECURITY = "SECURITY"

class DeviceType(str, enum.Enum):
    WATCHTOWER = "WATCHTOWER"
    SOILNODE = "SOILNODE"
    FEEDER = "FEEDER"
    WORKERTAG = "WORKERTAG"
    FENCEGRID = "FENCEGRID"
    HUB = "HUB"
    AQUASENSE = "AQUASENSE"

class DeviceStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    MAINTENANCE = "MAINTENANCE"
    UNREGISTERED = "UNREGISTERED"

class AlertSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"

class SectorType(str, enum.Enum):
    FIELD = "FIELD"
    PADDOCK = "PADDOCK"
    PEN = "PEN"
    POND = "POND"
    ROAD = "ROAD"
    STORAGE = "STORAGE"
    PERIMETER = "PERIMETER"

class MaintenanceType(str, enum.Enum):
    INSPECTION = "INSPECTION"
    CALIBRATION = "CALIBRATION"
    REPAIR = "REPAIR"
    REPLACEMENT = "REPLACEMENT"
    CLEANING = "CLEANING"
    FIRMWARE_UPDATE = "FIRMWARE_UPDATE"

class RuleTriggerType(str, enum.Enum):
    THRESHOLD = "THRESHOLD"
    SCHEDULE = "SCHEDULE"
    MANUAL = "MANUAL"
    DEVICE_STATE = "DEVICE_STATE"

# ── USERS ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    farm_memberships: Mapped[list["FarmUser"]] = relationship(back_populates="user")

# ── FARMS ─────────────────────────────────────────────────────────────────────

class Farm(Base):
    __tablename__ = "farms"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lng: Mapped[Optional[float]] = mapped_column(Float)
    boundary_geojson: Mapped[Optional[dict]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    members: Mapped[list["FarmUser"]] = relationship(back_populates="farm")
    sectors: Mapped[list["Sector"]] = relationship(back_populates="farm")
    devices: Mapped[list["Device"]] = relationship(back_populates="farm")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="farm")
    rules: Mapped[list["Rule"]] = relationship(back_populates="farm")

class FarmUser(Base):
    __tablename__ = "farm_users"
    farm_id: Mapped[str] = mapped_column(String, ForeignKey("farms.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    role: Mapped[FarmRole] = mapped_column(SAEnum(FarmRole), default=FarmRole.OPERATOR)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    farm: Mapped["Farm"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="farm_memberships")

# ── SECTORS ───────────────────────────────────────────────────────────────────

class Sector(Base):
    __tablename__ = "sectors"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    farm_id: Mapped[str] = mapped_column(String, ForeignKey("farms.id"), index=True)
    parent_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("sectors.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[SectorType] = mapped_column(SAEnum(SectorType), default=SectorType.FIELD)
    boundary_geojson: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    farm: Mapped["Farm"] = relationship(back_populates="sectors")
    devices: Mapped[list["Device"]] = relationship(back_populates="sector")

# ── DEVICES ───────────────────────────────────────────────────────────────────

class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    farm_id: Mapped[str] = mapped_column(String, ForeignKey("farms.id"), index=True)
    sector_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("sectors.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[DeviceType] = mapped_column(SAEnum(DeviceType))
    serial: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lng: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[DeviceStatus] = mapped_column(SAEnum(DeviceStatus), default=DeviceStatus.UNREGISTERED)
    battery_pct: Mapped[Optional[float]] = mapped_column(Float)
    firmware_ver: Mapped[Optional[str]] = mapped_column(String(64))
    api_key_hash: Mapped[Optional[str]] = mapped_column(String)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    farm: Mapped["Farm"] = relationship(back_populates="devices")
    sector: Mapped[Optional["Sector"]] = relationship(back_populates="devices")
    readings: Mapped[list["SensorReading"]] = relationship(back_populates="device")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="device")
    maintenance_events: Mapped[list["MaintenanceEvent"]] = relationship(back_populates="device")

# ── TELEMETRY ─────────────────────────────────────────────────────────────────

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    device_id: Mapped[str] = mapped_column(String, ForeignKey("devices.id"), index=True)
    farm_id: Mapped[str] = mapped_column(String, index=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(32))
    quality: Mapped[Optional[float]] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    device: Mapped["Device"] = relationship(back_populates="readings")

# ── ALERTS ────────────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    farm_id: Mapped[str] = mapped_column(String, ForeignKey("farms.id"), index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("devices.id"))
    sector_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("sectors.id"))
    severity: Mapped[AlertSeverity] = mapped_column(SAEnum(AlertSeverity), index=True)
    type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    context_json: Mapped[Optional[dict]] = mapped_column(JSON)
    status: Mapped[AlertStatus] = mapped_column(SAEnum(AlertStatus), default=AlertStatus.OPEN, index=True)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    farm: Mapped["Farm"] = relationship(back_populates="alerts")
    device: Mapped[Optional["Device"]] = relationship(back_populates="alerts")

# ── RULES ─────────────────────────────────────────────────────────────────────

class Rule(Base):
    __tablename__ = "rules"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    farm_id: Mapped[str] = mapped_column(String, ForeignKey("farms.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    trigger_type: Mapped[RuleTriggerType] = mapped_column(SAEnum(RuleTriggerType))
    trigger_config: Mapped[dict] = mapped_column(JSON)
    condition_json: Mapped[Optional[dict]] = mapped_column(JSON)
    action_json: Mapped[dict] = mapped_column(JSON)
    last_fired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    farm: Mapped["Farm"] = relationship(back_populates="rules")
    executions: Mapped[list["RuleExecution"]] = relationship(back_populates="rule")

class RuleExecution(Base):
    __tablename__ = "rule_executions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    rule_id: Mapped[str] = mapped_column(String, ForeignKey("rules.id"), index=True)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    result: Mapped[str] = mapped_column(String(32))  # SUCCESS | FAILED | SKIPPED
    context_json: Mapped[Optional[dict]] = mapped_column(JSON)
    rule: Mapped["Rule"] = relationship(back_populates="executions")

# ── MAINTENANCE ───────────────────────────────────────────────────────────────

class MaintenanceEvent(Base):
    __tablename__ = "maintenance_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    device_id: Mapped[str] = mapped_column(String, ForeignKey("devices.id"), index=True)
    farm_id: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[MaintenanceType] = mapped_column(SAEnum(MaintenanceType))
    description: Mapped[str] = mapped_column(Text)
    performed_by: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"))
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    next_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cost: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    device: Mapped["Device"] = relationship(back_populates="maintenance_events")

# ── WORKERS ───────────────────────────────────────────────────────────────────

class Worker(Base):
    __tablename__ = "workers"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    farm_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(128))
    tag_device_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("devices.id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class WorkerPresence(Base):
    __tablename__ = "worker_presence"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    worker_id: Mapped[str] = mapped_column(String, ForeignKey("workers.id"), index=True)
    sector_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("sectors.id"))
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lng: Mapped[Optional[float]] = mapped_column(Float)
    entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    exited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

# ── AUDIT LOG ─────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    farm_id: Mapped[Optional[str]] = mapped_column(String, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.id"))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[Optional[str]] = mapped_column(String)
    action: Mapped[str] = mapped_column(String(64))
    diff_json: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
