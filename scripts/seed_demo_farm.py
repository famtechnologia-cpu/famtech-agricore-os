#!/usr/bin/env python3
"""
Demo farm seed script — creates a realistic Famtech demo environment.
Run: python scripts/seed_demo_farm.py
"""
import asyncio
import secrets
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://agricore:agricore@localhost:5432/agricore"

async def seed():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))
    from models.all_models import Base, User, Farm, FarmUser, Sector, Device, Alert, Rule, Worker
    from models.all_models import FarmRole, DeviceType, DeviceStatus, AlertSeverity, AlertStatus
    from models.all_models import SectorType, RuleTriggerType, SensorReading
    from core.security import hash_password

    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as db:
        # ── Users ────────────────────────────────────────────────────────────
        owner = User(email="owner@greenvale.farm", hashed_password=hash_password("demo1234"),
                     full_name="Chidi Okafor", phone="+2348012345678", is_active=True)
        manager = User(email="manager@greenvale.farm", hashed_password=hash_password("demo1234"),
                       full_name="Amara Nwosu", phone="+2348098765432", is_active=True)
        tech = User(email="tech@greenvale.farm", hashed_password=hash_password("demo1234"),
                    full_name="Emeka Adeyemi", is_active=True)
        db.add_all([owner, manager, tech])
        await db.flush()

        # ── Farm ─────────────────────────────────────────────────────────────
        farm = Farm(
            name="Greenvale Agricultural Estate",
            timezone="Africa/Lagos",
            lat=7.3775, lng=3.9470,
            boundary_geojson={"type": "Polygon", "coordinates": [[[3.940, 7.370], [3.955, 7.370], [3.955, 7.385], [3.940, 7.385], [3.940, 7.370]]]},
        )
        db.add(farm)
        await db.flush()

        db.add_all([
            FarmUser(farm_id=farm.id, user_id=owner.id, role=FarmRole.OWNER),
            FarmUser(farm_id=farm.id, user_id=manager.id, role=FarmRole.MANAGER),
            FarmUser(farm_id=farm.id, user_id=tech.id, role=FarmRole.TECHNICIAN),
        ])

        # ── Sectors ──────────────────────────────────────────────────────────
        north = Sector(farm_id=farm.id, name="North Field", type=SectorType.FIELD)
        south = Sector(farm_id=farm.id, name="South Paddock", type=SectorType.PADDOCK)
        pond = Sector(farm_id=farm.id, name="Fish Pond Alpha", type=SectorType.POND)
        perimeter = Sector(farm_id=farm.id, name="East Perimeter", type=SectorType.PERIMETER)
        db.add_all([north, south, pond, perimeter])
        await db.flush()

        # ── Devices ──────────────────────────────────────────────────────────
        tower = Device(farm_id=farm.id, sector_id=north.id, name="Watchtower North",
                       type=DeviceType.WATCHTOWER, serial="FT-WT-001", lat=7.378, lng=3.948,
                       status=DeviceStatus.ONLINE, battery_pct=92.0, firmware_ver="2.1.4",
                       api_key_hash=hash_password(secrets.token_urlsafe(32)),
                       last_seen_at=datetime.now(timezone.utc))
        soil1 = Device(farm_id=farm.id, sector_id=north.id, name="Soilnode N-01",
                       type=DeviceType.SOILNODE, serial="FT-SN-001", lat=7.376, lng=3.945,
                       status=DeviceStatus.ONLINE, battery_pct=78.0, firmware_ver="1.3.2",
                       api_key_hash=hash_password(secrets.token_urlsafe(32)),
                       last_seen_at=datetime.now(timezone.utc))
        soil2 = Device(farm_id=farm.id, sector_id=south.id, name="Soilnode S-01",
                       type=DeviceType.SOILNODE, serial="FT-SN-002", lat=7.374, lng=3.947,
                       status=DeviceStatus.WARNING, battery_pct=21.0, firmware_ver="1.3.2",
                       api_key_hash=hash_password(secrets.token_urlsafe(32)),
                       last_seen_at=datetime.now(timezone.utc) - timedelta(minutes=5))
        feeder = Device(farm_id=farm.id, sector_id=south.id, name="Feedpro South",
                        type=DeviceType.FEEDER, serial="FT-FP-001", lat=7.373, lng=3.946,
                        status=DeviceStatus.ONLINE, battery_pct=None, firmware_ver="3.0.1",
                        api_key_hash=hash_password(secrets.token_urlsafe(32)),
                        last_seen_at=datetime.now(timezone.utc))
        buoy = Device(farm_id=farm.id, sector_id=pond.id, name="Aquasense Pond-A",
                      type=DeviceType.AQUASENSE, serial="FT-AQ-001", lat=7.375, lng=3.950,
                      status=DeviceStatus.ONLINE, battery_pct=65.0, firmware_ver="1.1.0",
                      api_key_hash=hash_password(secrets.token_urlsafe(32)),
                      last_seen_at=datetime.now(timezone.utc))
        fence = Device(farm_id=farm.id, sector_id=perimeter.id, name="Fencegrid E-01",
                       type=DeviceType.FENCEGRID, serial="FT-FG-001", lat=7.377, lng=3.953,
                       status=DeviceStatus.OFFLINE, battery_pct=8.0, firmware_ver="1.0.5",
                       api_key_hash=hash_password(secrets.token_urlsafe(32)),
                       last_seen_at=datetime.now(timezone.utc) - timedelta(hours=2))
        db.add_all([tower, soil1, soil2, feeder, buoy, fence])
        await db.flush()

        # ── Sensor Readings ──────────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        readings = []
        for i in range(24):  # 24h of readings at 1h intervals
            t = now - timedelta(hours=i)
            readings += [
                SensorReading(device_id=soil1.id, farm_id=farm.id, metric="soil_moisture", value=42.0 - i*0.5, unit="%", recorded_at=t),
                SensorReading(device_id=soil1.id, farm_id=farm.id, metric="soil_temp", value=28.0 + i*0.1, unit="°C", recorded_at=t),
                SensorReading(device_id=buoy.id, farm_id=farm.id, metric="ph", value=6.8 + (i % 3)*0.1, unit="pH", recorded_at=t),
                SensorReading(device_id=buoy.id, farm_id=farm.id, metric="do", value=7.2 - i*0.05, unit="mg/L", recorded_at=t),
            ]
        db.add_all(readings)

        # ── Alerts ───────────────────────────────────────────────────────────
        db.add_all([
            Alert(farm_id=farm.id, device_id=fence.id, sector_id=perimeter.id,
                  severity=AlertSeverity.CRITICAL, type="device_offline", status=AlertStatus.OPEN,
                  title="Fencegrid E-01 Offline", message="Device has not reported for 2 hours. Battery at 8%. Potential perimeter gap.",
                  context_json={"last_seen": "2h ago", "battery": "8%"}),
            Alert(farm_id=farm.id, device_id=soil2.id, sector_id=south.id,
                  severity=AlertSeverity.HIGH, type="low_battery", status=AlertStatus.OPEN,
                  title="Soilnode S-01 Low Battery", message="Battery at 21%. Schedule replacement within 48 hours.",
                  context_json={"battery_pct": 21}),
            Alert(farm_id=farm.id, device_id=soil1.id, sector_id=north.id,
                  severity=AlertSeverity.MEDIUM, type="threshold_breach", status=AlertStatus.ACKNOWLEDGED,
                  title="Soil Moisture Below Threshold", message="North Field moisture dropped to 30%. Irrigation may be required.",
                  context_json={"metric": "soil_moisture", "value": 30, "threshold": 35}),
        ])

        # ── Rules ────────────────────────────────────────────────────────────
        db.add_all([
            Rule(farm_id=farm.id, name="Low Soil Moisture Alert", enabled=True,
                 trigger_type=RuleTriggerType.THRESHOLD,
                 trigger_config={"device_id": soil1.id, "metric": "soil_moisture", "operator": "lt", "value": 35.0},
                 condition_json={"consecutive_readings": 3},
                 action_json={"create_alert": {"severity": "MEDIUM", "title": "Low soil moisture in North Field"}, "notify": ["in_app"]}),
            Rule(farm_id=farm.id, name="Critical Battery Alert", enabled=True,
                 trigger_type=RuleTriggerType.THRESHOLD,
                 trigger_config={"metric": "battery_pct", "operator": "lt", "value": 15.0},
                 action_json={"create_alert": {"severity": "HIGH", "title": "Device battery critical"}, "notify": ["in_app", "sms"]}),
        ])

        # ── Workers ──────────────────────────────────────────────────────────
        db.add_all([
            Worker(farm_id=farm.id, name="Taiwo Adeleke", role="Field Supervisor", active=True),
            Worker(farm_id=farm.id, name="Funke Balogun", role="Crop Technician", active=True),
            Worker(farm_id=farm.id, name="Musa Ibrahim", role="Security Guard", active=False),
        ])

        await db.commit()
        print(f"✅ Demo farm seeded: {farm.name}")
        print(f"   Farm ID: {farm.id}")
        print(f"   Login: owner@greenvale.farm / demo1234")
        print(f"   Login: manager@greenvale.farm / demo1234")

asyncio.run(seed())
