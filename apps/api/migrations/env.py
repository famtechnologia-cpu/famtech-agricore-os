"""
Alembic env.py — supports both sync (SQLite) and async (PostgreSQL) migrations.
DATABASE_URL from environment overrides alembic.ini.
"""
from __future__ import annotations
import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool, create_engine
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# ── Path setup ────────────────────────────────────────────────────────────────
_api_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

# Import all models (triggers registration with Base.metadata)
from core.base import Base  # noqa
import models.all_models  # noqa — registers all tables

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ── URL resolution ─────────────────────────────────────────────────────────────
def get_sync_url() -> str:
    """Convert async URL to sync equivalent for Alembic migrations."""
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url", ""))
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    url = url.replace("sqlite+aiosqlite:///", "sqlite:///")
    return url


# ── Offline migrations ─────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    context.configure(
        url=get_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migrations (sync engine) ───────────────────────────────────────────
def run_migrations_online() -> None:
    sync_engine = create_engine(get_sync_url(), poolclass=pool.NullPool)
    with sync_engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
