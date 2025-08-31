"""
Configuration management for AttentionSync API
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "AttentionSync"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    jwt_secret: str = Field(default="your-jwt-secret-here", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=1440, env="JWT_EXPIRE_MINUTES")  # 24 hours
    
    # Database
    database_url: str = Field(default="sqlite:///./attentionsync.db", env="DATABASE_URL")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # MinIO Object Storage
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ROOT_USER")
    minio_secret_key: str = Field(default="minioadmin", env="MINIO_ROOT_PASSWORD")
    minio_bucket: str = Field(default="attentionsync", env="MINIO_DEFAULT_BUCKETS")
    minio_secure: bool = Field(default=False)
    
    # AI Services
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Whisper Configuration
    whisper_model: str = Field(default="base", env="WHISPER_MODEL")
    whisper_device: str = Field(default="cpu", env="WHISPER_DEVICE")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    
    # Content Processing
    max_content_length: int = Field(default=1000000, env="MAX_CONTENT_LENGTH")
    summary_max_length: int = Field(default=200, env="SUMMARY_MAX_LENGTH")
    cluster_min_samples: int = Field(default=3, env="CLUSTER_MIN_SAMPLES")
    
    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="ALLOWED_ORIGINS"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()