"""
User model for AttentionSync
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text, JSON
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    """User model"""
    
    __tablename__ = "users"
    
    # Basic info
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    last_login_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Settings (JSON field for flexible configuration)
    settings = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    sources = relationship("Source", back_populates="user", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
    
    @property
    def display_name(self) -> str:
        """Get display name (full_name or username or email)"""
        return self.full_name or self.username or self.email.split("@")[0]
    
    def get_setting(self, key: str, default=None):
        """Get user setting by key"""
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value):
        """Set user setting"""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()