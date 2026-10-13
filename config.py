"""
Configuration settings for the application.
Uses pydantic-settings to load from environment variables or .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import Field


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./extra_hours.db"

    # JWT Authentication
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(60, gt=0)  # 1 hour
    jwt_refresh_token_expire_days: int = Field(30, gt=0)  # 30 days for refresh token

    # App
    app_name: str = "Extra Hours Management API"
    app_version: str = "1.0.0"
    debug: bool = False
    allow_registration: bool = True
    cors_origins: list[str] = [
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:4173", "http://127.0.0.1:4173",
        "http://localhost:3000", "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
