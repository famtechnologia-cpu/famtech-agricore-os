# AgriCore OS

> Famtech Farm Operating System — Production-grade MVP

## Quick Start

```bash
# Start all services
docker compose up -d

# Seed the demo farm
python scripts/seed_demo_farm.py

# Open the app
open http://localhost:3000
# Login: owner@greenvale.farm / demo1234
```

## Architecture

- **Backend:** FastAPI + PostgreSQL + Redis + MQTT
- **Frontend:** Next.js 14 PWA + Tailwind CSS
- **Edge:** SQLite + Mosquitto (runs on Famtech Hub)
- **Sync:** Store-and-forward, offline-first

## Repo Structure

```
apps/api/          # FastAPI backend
apps/web/          # Next.js frontend
apps/edge/         # Edge gateway (Hub)
scripts/           # Seed data, onboarding tools
infra/             # Docker, nginx configs
docs/              # Architecture, API, deployment
```

## Default Credentials (Demo)

| Role | Email | Password |
|---|---|---|
| Owner | owner@greenvale.farm | demo1234 |
| Manager | manager@greenvale.farm | demo1234 |
| Technician | tech@greenvale.farm | demo1234 |

## Development

```bash
# Backend only
cd apps/api && pip install -r requirements.txt
uvicorn main:app --reload

# Frontend only
cd apps/web && npm install && npm run dev

# API docs
open http://localhost:8000/docs
```

## Milestone Status

- [x] M1: Foundation — repo, database, auth, dashboard shell
- [ ] M2: Device & Telemetry — MQTT, real-time data
- [ ] M3: Map, Alerts, Rules — live farm map
- [ ] M4: Reports, Workers, Offline PWA
