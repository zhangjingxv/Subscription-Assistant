"""
Item model for AttentionSync - represents individual content items
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class Item(BaseModel):
    """Content item model"""
    
    __tablename__ = "items"
    
    # Basic content info
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)  # Full content
    summary = Column(Text, nullable=True)  # AI-generated summary
    url = Column(String(1000), nullable=False)
    
    # Metadata
    author = Column(String(200), nullable=True)
    published_at = Column(DateTime, nullable=True)
    language = Column(String(10), nullable=True)  # ISO language code
    word_count = Column(Integer, nullable=True)
    
    # Content analysis
    topics = Column(JSON, default=list, nullable=False)  # Extracted topics
    entities = Column(JSON, default=list, nullable=False)  # Named entities
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    importance_score = Column(Float, default=0.5, nullable=False)  # 0 to 1
    
    # Processing status
    is_processed = Column(Boolean, default=False, nullable=False)
    is_duplicate = Column(Boolean, default=False, nullable=False)
    duplicate_of_id = Column(Integer, ForeignKey("items.id"), nullable=True)
    
    # Content hash for deduplication
    content_hash = Column(String(64), index=True, nullable=True)
    
    # Media information
    has_video = Column(Boolean, default=False, nullable=False)
    has_audio = Column(Boolean, default=False, nullable=False)
    has_images = Column(Boolean, default=False, nullable=False)
    media_urls = Column(JSON, default=list, nullable=False)
    
    # User engagement (for personalization)
    view_count = Column(Integer, default=0, nullable=False)
    click_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    
    # Source relationship
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    source = relationship("Source", back_populates="items")
    
    # Self-referential relationship for duplicates
    duplicate_of = relationship("Item", remote_side=[id], backref="duplicates")
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_items_published_at", "published_at"),
        Index("ix_items_importance_score", "importance_score"),
        Index("ix_items_source_published", "source_id", "published_at"),
        Index("ix_items_processed", "is_processed"),
        Index("ix_items_duplicate", "is_duplicate"),
    )
    
    def __repr__(self):
        return f"<Item(id={self.id}, title='{self.title[:50]}...', source_id={self.source_id})>"
    
    @property
    def is_recent(self) -> bool:
        """Check if item is from the last 24 hours"""
        if not self.published_at:
            return False
        return (datetime.utcnow() - self.published_at).days < 1
    
    @property
    def engagement_score(self) -> float:
        """Calculate engagement score"""
        return (
            self.view_count * 0.1 +
            self.click_count * 0.5 +
            self.share_count * 1.0
        )
    
    def increment_view(self):
        """Increment view count"""
        self.view_count += 1
    
    def increment_click(self):
        """Increment click count"""
        self.click_count += 1
    
    def increment_share(self):
        """Increment share count"""
        self.share_count += 1
    
    def add_topic(self, topic: str, confidence: float = 1.0):
        """Add a topic to the item"""
        if self.topics is None:
            self.topics = []
        
        # Check if topic already exists
        for existing_topic in self.topics:
            if existing_topic.get("name") == topic:
                # Update confidence if higher
                if confidence > existing_topic.get("confidence", 0):
                    existing_topic["confidence"] = confidence
                return
        
        # Add new topic
        self.topics.append({
            "name": topic,
            "confidence": confidence
        })
    
    def add_entity(self, entity: str, entity_type: str, confidence: float = 1.0):
        """Add a named entity to the item"""
        if self.entities is None:
            self.entities = []
        
        # Check if entity already exists
        for existing_entity in self.entities:
            if (existing_entity.get("name") == entity and 
                existing_entity.get("type") == entity_type):
                return
        
        # Add new entity
        self.entities.append({
            "name": entity,
            "type": entity_type,
            "confidence": confidence
        })