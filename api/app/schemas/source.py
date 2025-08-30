"""
Source schemas for API validation
"""

from datetime import datetime
from typing import Dict, Optional, Any

from pydantic import BaseModel, HttpUrl, Field, validator

from app.models.source import SourceType, SourceStatus


class SourceBase(BaseModel):
    """Base source schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    url: HttpUrl
    source_type: SourceType
    fetch_interval_minutes: int = Field(default=60, ge=5, le=10080)  # 5 min to 1 week


class SourceCreate(SourceBase):
    """Source creation schema"""
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @validator("config")
    def validate_config(cls, v, values):
        """Validate configuration based on source type"""
        source_type = values.get("source_type")
        
        if source_type == SourceType.RSS:
            # RSS specific validation
            pass
        elif source_type == SourceType.VIDEO:
            # Video specific validation
            if "platform" not in v:
                v["platform"] = "youtube"  # default
        
        return v


class SourceUpdate(BaseModel):
    """Source update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    url: Optional[HttpUrl] = None
    fetch_interval_minutes: Optional[int] = Field(None, ge=5, le=10080)
    status: Optional[SourceStatus] = None
    config: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None


class SourceResponse(SourceBase):
    """Source response schema"""
    id: int
    status: SourceStatus
    user_id: int
    
    # Statistics
    total_items: int
    success_count: int
    error_count: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_fetched_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    
    # Configuration
    config: Dict[str, Any]
    headers: Dict[str, str]
    
    class Config:
        from_attributes = True
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.success_count / total


class SourceStats(BaseModel):
    """Source statistics schema"""
    total_sources: int
    active_sources: int
    paused_sources: int
    error_sources: int
    total_items_today: int
    avg_success_rate: float