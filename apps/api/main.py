from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine
from .models.all_models import Base
from .routers import auth, farms, devices, alerts, rules, maintenance, workers, ws, sectors

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="AgriCore OS API",
    description="Farm operating system backend — Famtech",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.famtech.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(farms.router)
app.include_router(devices.router)
app.include_router(devices.telemetry_router)
app.include_router(alerts.router)
app.include_router(rules.router)
app.include_router(maintenance.router)
app.include_router(workers.router)
app.include_router(ws.router)
app.include_router(sectors.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "agricore-api"}
