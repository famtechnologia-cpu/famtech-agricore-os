"""
Core tests for AgriCore OS.
Run: pip install pytest pytest-asyncio httpx && pytest apps/api/tests/
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Use in-memory SQLite for tests
TEST_DB = "sqlite+aiosqlite:///:memory:"

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture(scope="session")
async def app():
    from core.config import settings
    settings.DATABASE_URL = TEST_DB
    from main import app as fastapi_app
    from core.database import engine, Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return fastapi_app

@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest_asyncio.fixture
async def auth_headers(client):
    # Register + login
    await client.post("/auth/register", json={
        "email": "test@farm.io", "password": "test1234", "full_name": "Test User"
    })
    res = await client.post("/auth/login", json={"email": "test@farm.io", "password": "test1234"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ── Auth tests ────────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_health(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

@pytest.mark.anyio
async def test_register_and_login(client):
    res = await client.post("/auth/register", json={
        "email": "farmer@greenvale.io", "password": "strongpass", "full_name": "John Okafor"
    })
    assert res.status_code == 201
    res = await client.post("/auth/login", json={"email": "farmer@greenvale.io", "password": "strongpass"})
    assert res.status_code == 200
    assert "access_token" in res.json()

@pytest.mark.anyio
async def test_invalid_login(client):
    res = await client.post("/auth/login", json={"email": "nobody@x.io", "password": "wrong"})
    assert res.status_code == 401

@pytest.mark.anyio
async def test_me_requires_auth(client):
    res = await client.get("/auth/me")
    assert res.status_code == 403

# ── Farm tests ────────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_create_farm(client, auth_headers):
    res = await client.post("/farms", json={"name": "Test Farm", "timezone": "UTC"}, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["name"] == "Test Farm"

@pytest.mark.anyio
async def test_farm_summary(client, auth_headers):
    # Create farm first
    farm_res = await client.post("/farms", json={"name": "Summary Farm"}, headers=auth_headers)
    farm_id = farm_res.json()["id"]
    res = await client.get(f"/farms/{farm_id}/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "device_count" in data
    assert "open_alerts" in data
    assert data["device_count"] == 0

# ── Device tests ──────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_register_device(client, auth_headers):
    farm_res = await client.post("/farms", json={"name": "Device Farm"}, headers=auth_headers)
    farm_id = farm_res.json()["id"]
    res = await client.post(
        f"/farms/{farm_id}/devices/register",
        json={"name": "Soilnode 1", "type": "SOILNODE", "serial": "FT-SN-TEST-001"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Soilnode 1"
    assert "api_key" in data  # Only returned at registration
    assert data["status"] == "OFFLINE"

@pytest.mark.anyio
async def test_device_list(client, auth_headers):
    farm_res = await client.post("/farms", json={"name": "List Farm"}, headers=auth_headers)
    farm_id = farm_res.json()["id"]
    await client.post(f"/farms/{farm_id}/devices/register", json={"name": "Tower 1", "type": "WATCHTOWER"}, headers=auth_headers)
    res = await client.get(f"/farms/{farm_id}/devices", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

# ── Alert tests ───────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_alert_list_empty(client, auth_headers):
    farm_res = await client.post("/farms", json={"name": "Alert Farm"}, headers=auth_headers)
    farm_id = farm_res.json()["id"]
    res = await client.get(f"/farms/{farm_id}/alerts", headers=auth_headers)
    assert res.status_code == 200
    assert res.json() == []

# ── Rules tests ───────────────────────────────────────────────────────────────
@pytest.mark.anyio
async def test_create_rule(client, auth_headers):
    farm_res = await client.post("/farms", json={"name": "Rule Farm"}, headers=auth_headers)
    farm_id = farm_res.json()["id"]
    res = await client.post(f"/farms/{farm_id}/rules", json={
        "name": "Low moisture alert",
        "trigger_type": "THRESHOLD",
        "trigger_config": {"metric": "soil_moisture", "operator": "lt", "value": 30},
        "action_json": {"create_alert": {"severity": "MEDIUM", "title": "Low moisture"}, "notify": ["in_app"]},
    }, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["enabled"] == True

@pytest.mark.anyio
async def test_toggle_rule(client, auth_headers):
    farm_res = await client.post("/farms", json={"name": "Toggle Farm"}, headers=auth_headers)
    farm_id = farm_res.json()["id"]
    rule_res = await client.post(f"/farms/{farm_id}/rules", json={
        "name": "Toggle me",
        "trigger_type": "THRESHOLD",
        "trigger_config": {"metric": "battery_pct", "operator": "lt", "value": 20},
        "action_json": {"create_alert": {"severity": "HIGH", "title": "Low battery"}, "notify": ["in_app"]},
    }, headers=auth_headers)
    rule_id = rule_res.json()["id"]
    res = await client.post(f"/farms/{farm_id}/rules/{rule_id}/toggle", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["enabled"] == False  # Was True, now False

# ── Rules engine unit tests ────────────────────────────────────────────────────
def test_rule_operator_lt():
    from services.rules_engine import OPERATORS
    assert OPERATORS["lt"](20, 30) == True
    assert OPERATORS["lt"](40, 30) == False

def test_rule_operator_gt():
    from services.rules_engine import OPERATORS
    assert OPERATORS["gt"](40, 30) == True
    assert OPERATORS["gt"](20, 30) == False
