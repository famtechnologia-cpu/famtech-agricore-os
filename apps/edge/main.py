"""
Edge gateway service — runs on the Famtech Hub (Raspberry Pi or industrial PC).
Provides a local FastAPI server that works fully offline.
Syncs to cloud when connectivity is available.
"""
import asyncio
import logging
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
import sqlite3
import json

log = logging.getLogger("edge-gateway")
logging.basicConfig(level=logging.INFO)

CLOUD_URL = "http://api.famtech.io"  # Override via env
SYNC_INTERVAL = 60  # seconds

app = FastAPI(title="Famtech Hub — Edge Gateway", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── Local SQLite DB ────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect("edge_local.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            operation TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            synced_at TEXT,
            retry_count INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS local_readings (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            farm_id TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            recorded_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        );
    """)
    db.commit()
    db.close()

@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(sync_loop())

# ── Local telemetry endpoint ───────────────────────────────────────────────────
@app.post("/local/telemetry")
async def local_telemetry(payload: dict):
    """Accepts telemetry from devices on the local network."""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()
    for r in payload.get("readings", []):
        import uuid
        db.execute(
            "INSERT OR IGNORE INTO local_readings (id, device_id, farm_id, metric, value, unit, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), payload["device_id"], payload.get("farm_id", ""), r["metric"], r["value"], r.get("unit"), r.get("recorded_at", now))
        )
    # Queue for cloud sync
    db.execute(
        "INSERT INTO sync_queue (entity_type, operation, payload, created_at) VALUES (?, ?, ?, ?)",
        ("telemetry", "push", json.dumps(payload), now)
    )
    db.commit()
    db.close()
    return {"status": "queued", "readings": len(payload.get("readings", []))}

@app.get("/local/status")
async def local_status():
    db = get_db()
    pending = db.execute("SELECT COUNT(*) as n FROM sync_queue WHERE synced_at IS NULL").fetchone()["n"]
    db.close()
    return {"status": "running", "pending_sync": pending, "timestamp": datetime.now(timezone.utc).isoformat()}

# ── Cloud sync loop ────────────────────────────────────────────────────────────
async def sync_loop():
    while True:
        await asyncio.sleep(SYNC_INTERVAL)
        await sync_to_cloud()

async def sync_to_cloud():
    db = get_db()
    pending = db.execute(
        "SELECT * FROM sync_queue WHERE synced_at IS NULL AND retry_count < 5 ORDER BY created_at LIMIT 100"
    ).fetchall()

    if not pending:
        db.close()
        return

    log.info(f"Syncing {len(pending)} records to cloud...")
    async with httpx.AsyncClient(timeout=15) as client:
        for row in pending:
            try:
                resp = await client.post(f"{CLOUD_URL}/sync/push", json={
                    "entity_type": row["entity_type"],
                    "operation": row["operation"],
                    "payload": json.loads(row["payload"]),
                })
                if resp.status_code in (200, 201):
                    db.execute(
                        "UPDATE sync_queue SET synced_at = ? WHERE id = ?",
                        (datetime.now(timezone.utc).isoformat(), row["id"])
                    )
                else:
                    db.execute("UPDATE sync_queue SET retry_count = retry_count + 1 WHERE id = ?", (row["id"],))
            except Exception as e:
                log.warning(f"Sync failed for record {row['id']}: {e}")
                db.execute("UPDATE sync_queue SET retry_count = retry_count + 1 WHERE id = ?", (row["id"],))

    db.commit()
    db.close()
    log.info("Sync complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
