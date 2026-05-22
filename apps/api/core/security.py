from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from fastapi import HTTPException, status
import hashlib
import hmac
import secrets as _secrets
from .config import settings

def hash_password(password: str) -> str:
    """PBKDF2-SHA256 password hash — upgrade to argon2 in production."""
    salt = _secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260_000)
    return f"pbkdf2$sha256$260000${salt}${key.hex()}"

def verify_password(plain: str, hashed: str) -> bool:
    try:
        _, algo, iterations, salt, stored = hashed.split("$")
        key = hashlib.pbkdf2_hmac(algo, plain.encode(), salt.encode(), int(iterations))
        return hmac.compare_digest(key.hex(), stored)
    except Exception:
        return False

def create_access_token(data: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire, "type": "access"}, settings.SECRET_KEY, settings.ALGORITHM)

def create_refresh_token(data: dict[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({**data, "exp": expire, "type": "refresh"}, settings.SECRET_KEY, settings.ALGORITHM)

def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
