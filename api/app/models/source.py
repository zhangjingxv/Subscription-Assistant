"""
Source model for AttentionSync - represents information sources
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class SourceType(str, enum.Enum):
    """Source type enumeration"""
    RSS = "rss"
    API = "api"
    WEBPAGE = "webpage"
    VIDEO = "video"
    PODCAST = "podcast"
    SOCIAL = "social"
    EMAIL = "email"
    WEBHOOK = "webhook"


class SourceStatus(str, enum.Enum):
    """Source status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class Source(BaseModel):
    """Information source model"""
    
    __tablename__ = "sources"
    
    # Basic info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    
    # Configuration
    config = Column(JSON, default=dict, nullable=False)  # Flexible configuration
    headers = Column(JSON, default=dict, nullable=False)  # Custom headers
    
    # Status and metadata
    status = Column(SQLEnum(SourceStatus), default=SourceStatus.ACTIVE, nullable=False)
    last_fetched_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    last_error_message = Column(Text, nullable=True)
    
    # Fetch statistics
    total_items = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    
    # Schedule configuration
    fetch_interval_minutes = Column(Integer, default=60, nullable=False)  # Default: 1 hour
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="sources")
    
    # Items relationship
    items = relationship("Item", back_populates="source", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', type='{self.source_type}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if source is active"""
        return self.status == SourceStatus.ACTIVE
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    def record_success(self):
        """Record successful fetch"""
        self.last_fetched_at = datetime.utcnow()
        self.last_success_at = datetime.utcnow()
        self.success_count += 1
        self.last_error_message = None
    
    def record_error(self, error_message: str):
        """Record fetch error"""
        self.last_fetched_at = datetime.utcnow()
        self.last_error_at = datetime.utcnow()
        self.last_error_message = error_message
        self.error_count += 1
        
        # Auto-disable source after too many consecutive errors
        if self.error_count > 10 and self.success_rate < 0.1:
            self.status = SourceStatus.ERROR
    
    def get_config(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value):
        """Set configuration value"""
        if self.config is None:
            self.config = {}
        self.config[key] = value