from __future__ import annotations
"""
Standalone Base declaration — no imports from config or engine.
This allows Alembic to import Base without needing DATABASE_URL at import time.
"""
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
