"""
Item schemas for API validation
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, HttpUrl, Field


class ItemBase(BaseModel):
    """Base item schema"""
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    url: HttpUrl
    author: Optional[str] = Field(None, max_length=200)
    published_at: Optional[datetime] = None
    language: Optional[str] = Field(None, max_length=10)


class ItemCreate(ItemBase):
    """Item creation schema"""
    source_id: int
    content_hash: Optional[str] = None
    topics: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    entities: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    media_urls: Optional[List[str]] = Field(default_factory=list)


class ItemUpdate(BaseModel):
    """Item update schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = None
    importance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    topics: Optional[List[Dict[str, Any]]] = None
    entities: Optional[List[Dict[str, Any]]] = None


class ItemResponse(ItemBase):
    """Item response schema"""
    id: int
    summary: Optional[str] = None
    source_id: int
    
    # Analysis results
    topics: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    sentiment_score: Optional[float] = None
    importance_score: float
    
    # Processing status
    is_processed: bool
    is_duplicate: bool
    duplicate_of_id: Optional[int] = None
    
    # Media info
    has_video: bool
    has_audio: bool
    has_images: bool
    media_urls: List[str]
    
    # Statistics
    view_count: int
    click_count: int
    share_count: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ItemSummary(BaseModel):
    """Simplified item summary for lists"""
    id: int
    title: str
    summary: Optional[str] = None
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    importance_score: float
    topics: List[str]  # Just topic names
    source_name: str
    
    class Config:
        from_attributes = True


class ItemFilter(BaseModel):
    """Item filtering parameters"""
    source_ids: Optional[List[int]] = None
    topics: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_importance: Optional[float] = Field(None, ge=0.0, le=1.0)
    has_summary: Optional[bool] = None
    language: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)