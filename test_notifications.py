import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from apps.api.models.all_models import Base, Farm, User, FarmUser, FarmRole, Device, DeviceType, Rule, RuleTriggerType, SensorReading
from apps.api.services.rules_engine import _evaluate_threshold_rule

logging.basicConfig(level=logging.DEBUG)

async def run_test():
    # Use an in-memory SQLite DB for the test
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as db:
        # 1. Setup Farm & User
        farm = Farm(name="Test Farm")
        db.add(farm)
        await db.flush()
        
        user = User(email="farmer@test.com", full_name="Test Farmer", hashed_password="pw", phone="+1234567890")
        db.add(user)
        await db.flush()
        
        fu = FarmUser(farm_id=farm.id, user_id=user.id, role=FarmRole.OWNER)
        db.add(fu)
        
        # 2. Setup Device
        device = Device(farm_id=farm.id, name="Test Sensor", type=DeviceType.SOILNODE)
        db.add(device)
        await db.flush()
        
        # 3. Setup Rule with SMS and Email action
        rule = Rule(
            farm_id=farm.id,
            name="Low Moisture Alert",
            enabled=True,
            trigger_type=RuleTriggerType.THRESHOLD,
            trigger_config={"device_id": device.id, "metric": "moisture", "operator": "lt", "value": 20.0},
            condition_json={"consecutive_readings": 1},
            action_json={
                "create_alert": {"severity": "HIGH", "title": "Soil Moisture Low!"},
                "send_sms": {"roles": ["OWNER"]},
                "send_email": {"roles": ["OWNER"]}
            }
        )
        db.add(rule)
        await db.flush()
        
        # 4. Insert breaching SensorReading
        from datetime import datetime, timezone
        reading = SensorReading(
            device_id=device.id,
            farm_id=farm.id,
            metric="moisture",
            value=15.0,
            recorded_at=datetime.now(timezone.utc)
        )
        db.add(reading)
        await db.flush()
        
        # 5. Evaluate Rule
        await _evaluate_threshold_rule(rule, device.id, farm.id, db)
        
        # Give asyncio tasks a moment to run
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(run_test())
