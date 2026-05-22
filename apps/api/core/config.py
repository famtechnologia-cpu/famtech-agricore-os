from __future__ import annotations
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_32_BYTE_SECRET"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    DATABASE_URL: str = "postgresql+asyncpg://agricore:agricore@localhost:5432/agricore"
    REDIS_URL: str = "redis://localhost:6379/0"
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883

    FIRST_SUPERUSER_EMAIL: str = "admin@famtech.io"
    FIRST_SUPERUSER_PASSWORD: str = "changeme"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "alerts@famtech.io"

settings = Settings()
