"""
User preference model for personalization
"""

from sqlalchemy import Column, Float, ForeignKey, Integer, String, JSON, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class UserPreference(BaseModel):
    """User preference model for personalization engine"""
    
    __tablename__ = "user_preferences"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="preferences")
    
    # Preference type and key
    preference_type = Column(String(50), nullable=False)  # topic, source, author, etc.
    preference_key = Column(String(200), nullable=False)  # specific value
    
    # Preference score (-1 to 1, where 1 is strong positive preference)
    score = Column(Float, default=0.0, nullable=False)
    
    # Interaction counts for score calculation
    positive_interactions = Column(Integer, default=0, nullable=False)  # clicks, saves, shares
    negative_interactions = Column(Integer, default=0, nullable=False)  # skips, dislikes
    
    # Additional metadata
    preference_metadata = Column(JSON, default=dict, nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_user_preferences_user_type", "user_id", "preference_type"),
        Index("ix_user_preferences_score", "score"),
        Index("ix_user_preferences_key", "preference_key"),
    )
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id}, type='{self.preference_type}', key='{self.preference_key}', score={self.score})>"
    
    def add_positive_interaction(self, weight: float = 1.0):
        """Add positive interaction and update score"""
        self.positive_interactions += 1
        self._update_score(weight)
    
    def add_negative_interaction(self, weight: float = 1.0):
        """Add negative interaction and update score"""
        self.negative_interactions += 1
        self._update_score(-weight)
    
    def _update_score(self, interaction_weight: float):
        """Update preference score based on interactions"""
        total_interactions = self.positive_interactions + self.negative_interactions
        
        if total_interactions == 0:
            self.score = 0.0
            return
        
        # Calculate weighted score
        positive_weight = self.positive_interactions
        negative_weight = self.negative_interactions
        
        # Apply learning rate decay for older preferences
        learning_rate = min(1.0, 10.0 / total_interactions)
        
        # Update score with momentum
        raw_score = (positive_weight - negative_weight) / total_interactions
        self.score = self.score * (1 - learning_rate) + raw_score * learning_rate
        
        # Clamp to [-1, 1] range
        self.score = max(-1.0, min(1.0, self.score))
    
    @classmethod
    def create_or_update(cls, user_id: int, preference_type: str, preference_key: str, 
                        interaction_weight: float = 1.0):
        """Create new preference or update existing one"""
        # This would typically be implemented in a service layer
        pass