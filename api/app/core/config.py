"""
Simple configuration for AttentionSync
Following Unix philosophy: Do one thing well
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Minimal application settings - no magic, just essentials"""
    
    # Application
    app_name: str = "AttentionSync"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours
    
    # Database - SQLite by default, zero config
    database_url: str = "sqlite:///./attentionsync.db"
    
    # Redis (optional)
    redis_url: Optional[str] = None
    
    # CORS
    allowed_origins: list = ["http://localhost:3000", "http://localhost:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Simple helper functions
def is_development() -> bool:
    """Check if running in development mode"""
    return get_settings().environment == "development"


def is_production() -> bool:
    """Check if running in production mode"""
    return get_settings().environment == "production"