"""
MQTT telemetry listener — subscribes to device topics and writes to DB.
Runs as a background service alongside the FastAPI app.
Topic format: famtech/{farm_id}/{device_id}/telemetry
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from aiomqtt import Client as MQTTClient, MqttError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.config import settings
from core.security import verify_password
from models.all_models import Device, DeviceStatus, SensorReading

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mqtt-listener")

engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def process_message(topic: str, payload: bytes):
    parts = topic.split("/")
    if len(parts) < 4 or parts[0] != "famtech":
        return
    farm_id, device_id = parts[1], parts[2]
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        log.warning(f"Bad JSON from {device_id}")
        return

    async with Session() as db:
        device = (await db.execute(
            select(Device).where(Device.id == device_id, Device.farm_id == farm_id)
        )).scalar_one_or_none()
        if not device:
            log.warning(f"Unknown device: {device_id}")
            return

        now = datetime.now(timezone.utc)
        readings = []
        for r in data.get("readings", []):
            readings.append(SensorReading(
                device_id=device.id,
                farm_id=farm_id,
                metric=r["metric"],
                value=float(r["value"]),
                unit=r.get("unit"),
                quality=r.get("quality", 1.0),
                recorded_at=datetime.fromisoformat(r["recorded_at"]) if "recorded_at" in r else now,
            ))
        if readings:
            db.add_all(readings)

        device.last_seen_at = now
        device.status = DeviceStatus.ONLINE
        if data.get("battery_pct") is not None:
            device.battery_pct = data["battery_pct"]
            if device.battery_pct < 15:
                device.status = DeviceStatus.WARNING
        if data.get("firmware_ver"):
            device.firmware_ver = data["firmware_ver"]

        await db.commit()
        log.info(f"[{device.name}] {len(readings)} readings ingested")


async def run_listener():
    log.info(f"Connecting to MQTT at {settings.MQTT_HOST}:{settings.MQTT_PORT}")
    async with MQTTClient(settings.MQTT_HOST, settings.MQTT_PORT) as client:
        await client.subscribe("famtech/#")
        log.info("Subscribed to famtech/#")
        async for message in client.messages:
            asyncio.create_task(process_message(str(message.topic), message.payload))


async def main():
    while True:
        try:
            await run_listener()
        except MqttError as e:
            log.error(f"MQTT error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
