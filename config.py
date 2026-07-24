"""
Configuration settings for the application.
Uses pydantic-settings to load from environment variables or .env file.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./extra_hours.db"

    # JWT Authentication
    jwt_secret_key: str = "change-this-to-a-very-long-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60  # 1 hour
    jwt_refresh_token_expire_days: int = 30  # 30 days for refresh token

    # App
    app_name: str = "Extra Hours Management API"
    app_version: str = "1.0.0"
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
