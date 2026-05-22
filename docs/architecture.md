# AgriCore OS — Architecture & API Reference

## System Architecture

```
┌─────────────────────────────────────────────┐
│              CLOUD (famtech.io)              │
│  Next.js PWA  ←→  FastAPI  ←→  PostgreSQL   │
│                     ↕                        │
│              MQTT  +  Redis  +  WS           │
└──────────────────────┬──────────────────────┘
                       │ HTTPS (store-and-forward)
┌──────────────────────▼──────────────────────┐
│           EDGE (Famtech Hub)                 │
│  FastAPI :8001  ←→  SQLite  ←→  Mosquitto   │
│  Sync daemon runs every 60s                  │
└──────────────────────┬──────────────────────┘
                       │ BLE / LoRa / Wi-Fi / 4G
┌──────────────────────▼──────────────────────┐
│  FIELD DEVICES                               │
│  Watchtower · Soilnode · Feeder · Fencegrid  │
└─────────────────────────────────────────────┘
```

## Roles & Permissions

| Role | Can Do |
|---|---|
| OWNER | Everything |
| MANAGER | All except delete farm |
| OPERATOR | View, ack/resolve alerts |
| TECHNICIAN | Register devices, log maintenance |
| SECURITY | View alerts, view cameras |

## API Base URL
- Cloud: `http://localhost:8000` (dev) / `https://api.famtech.io` (prod)
- Edge: `http://hub.local:8001`
- Docs: `http://localhost:8000/docs`

## Key Endpoints

### Auth
```
POST /auth/login          → {access_token, refresh_token}
POST /auth/refresh
POST /auth/register
GET  /auth/me
```

### Farms
```
GET  /farms               → List user's farms
POST /farms               → Create farm
GET  /farms/{id}/summary  → Dashboard KPIs
POST /farms/{id}/invite   → Invite user by email + role
```

### Devices
```
GET  /farms/{id}/devices
POST /farms/{id}/devices/register    → Returns api_key (once only)
GET  /farms/{id}/devices/{device_id}/readings?metric=&limit=
POST /devices/telemetry              → Device push (ApiKey auth)
```

### Alerts
```
GET  /farms/{id}/alerts?status=&severity=
POST /farms/{id}/alerts/{aid}/acknowledge
POST /farms/{id}/alerts/{aid}/resolve
```

### Rules
```
GET  /farms/{id}/rules
POST /farms/{id}/rules
POST /farms/{id}/rules/{rid}/toggle
GET  /farms/{id}/rules/{rid}/executions
```

### Sectors
```
GET  /farms/{id}/sectors
POST /farms/{id}/sectors
PATCH /farms/{id}/sectors/{sid}
```

### Workers
```
GET  /farms/{id}/workers
GET  /farms/{id}/workers/presence
POST /farms/{id}/workers
```

### Maintenance
```
GET  /farms/{id}/maintenance
POST /farms/{id}/maintenance
GET  /farms/{id}/maintenance/device/{device_id}
```

### WebSocket
```
WS   /ws/{farm_id}?token=<jwt>

Events received:
  CONNECTED      → Initial connection confirmation
  ALERT_CREATED  → New alert fired
  DEVICE_UPDATED → Device status or reading changed
  TELEMETRY      → New sensor readings batch
```

## Device Telemetry Format

Devices push to `POST /devices/telemetry`:
```json
{
  "device_id": "dev_xxx",
  "battery_pct": 78.5,
  "firmware_ver": "2.1.4",
  "readings": [
    {"metric": "soil_moisture", "value": 42.3, "unit": "%"},
    {"metric": "soil_temp", "value": 28.1, "unit": "°C"}
  ]
}
```

Header: `Authorization: ApiKey <api_key>`

Or via MQTT: `famtech/{farm_id}/{device_id}/telemetry` (same JSON body)

## Offline Strategy

1. Browser caches app shell via service worker (`/public/sw.js`)
2. Last-known devices/alerts stored in IndexedDB via Dexie (`/lib/offline/db.ts`)
3. Failed API calls queue in IndexedDB as `offlineActions`
4. On reconnect, background sync replays queued actions
5. Edge Hub stores all telemetry in SQLite, syncs to cloud when online

## Deployment

### Cloud (full stack)
```bash
docker compose up -d
python scripts/seed_demo_farm.py
```

### Edge (Hub only, offline)
```bash
docker compose -f docker-compose.edge.yml up -d
```

### Onboard a new device
```bash
python scripts/onboard_device.py \
  --name "Soilnode N-02" \
  --type SOILNODE \
  --farm <farm_id> \
  --token <jwt>
```
