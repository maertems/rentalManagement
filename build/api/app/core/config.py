from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "mysql+asyncmy://rental:rental@mysql:3306/rental"
    JWT_SECRET: str = "change-me-in-production-please"
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60
    JWT_REFRESH_EXPIRES_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    # Regex for CORS origins. Default accepts any LAN host on any port (HTTP only).
    # Override via env to tighten in production.
    CORS_ORIGIN_REGEX: str = (
        r"^http://(localhost|127\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+)(:\d+)?$"
    )

    # Cookie flags (toggle Secure=True in production over HTTPS)
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str | None = None

    # Admin bootstrap (used on startup if no admin exists)
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_PASSWORD: str = "admin123"

    # SMTP — envoi des documents PDF
    SMTP_HOST: str = "10.0.10.102"
    SMTP_PORT: int = 25
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""


settings = Settings()
