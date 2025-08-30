"""
Collection model for AttentionSync - user's saved items and folders
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, Table
from sqlalchemy.orm import relationship

from .base import BaseModel

# Association table for many-to-many relationship between collections and items
collection_items = Table(
    'collection_items',
    BaseModel.metadata,
    Column('collection_id', Integer, ForeignKey('collections.id'), primary_key=True),
    Column('item_id', Integer, ForeignKey('items.id'), primary_key=True)
)


class Collection(BaseModel):
    """Collection/folder model for organizing saved items"""
    
    __tablename__ = "collections"
    
    # Basic info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    is_public = Column(Boolean, default=False, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Default "Saved" collection
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="collections")
    
    # Items relationship (many-to-many)
    items = relationship("Item", secondary=collection_items, backref="collections")
    
    def __repr__(self):
        return f"<Collection(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    @property
    def item_count(self) -> int:
        """Get number of items in collection"""
        return len(self.items) if self.items else 0