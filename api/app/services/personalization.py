"""
Personalization service for AttentionSync
Handles user preference learning and content scoring
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from app.models.user import User
from app.models.item import Item
from app.models.user_preference import UserPreference

logger = structlog.get_logger()


class PersonalizationService:
    """Service for handling personalization and recommendations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def score_items_for_user(self, user_id: int, items: List[Item]) -> List[Dict[str, Any]]:
        """Score items for a specific user based on their preferences"""
        if not items:
            return []
        
        # Get user preferences
        preferences_query = select(UserPreference).where(UserPreference.user_id == user_id)
        result = await self.db.execute(preferences_query)
        preferences = result.scalars().all()
        
        # Create preference lookup dictionaries
        topic_prefs = {}
        source_prefs = {}
        author_prefs = {}
        
        for pref in preferences:
            if pref.preference_type == "topic":
                topic_prefs[pref.preference_key] = pref.score
            elif pref.preference_type == "source":
                source_prefs[pref.preference_key] = pref.score
            elif pref.preference_type == "author":
                author_prefs[pref.preference_key] = pref.score
        
        # Score each item
        scored_items = []
        for item in items:
            score = await self._calculate_item_score(
                item, topic_prefs, source_prefs, author_prefs
            )
            
            scored_items.append({
                "item": item,
                "score": score,
                "factors": self._get_score_factors(item, topic_prefs, source_prefs, author_prefs)
            })
        
        return scored_items
    
    async def _calculate_item_score(
        self, 
        item: Item, 
        topic_prefs: Dict[str, float],
        source_prefs: Dict[str, float],
        author_prefs: Dict[str, float]
    ) -> float:
        """Calculate personalized score for an item"""
        base_score = item.importance_score
        
        # Topic relevance score
        topic_score = 0.0
        if item.topics:
            topic_scores = []
            for topic_data in item.topics:
                if isinstance(topic_data, dict) and "name" in topic_data:
                    topic_name = topic_data["name"]
                    confidence = topic_data.get("confidence", 1.0)
                    pref_score = topic_prefs.get(topic_name, 0.0)
                    topic_scores.append(pref_score * confidence)
            
            if topic_scores:
                topic_score = sum(topic_scores) / len(topic_scores)
        
        # Source preference score
        source_score = source_prefs.get(str(item.source_id), 0.0)
        
        # Author preference score
        author_score = 0.0
        if item.author:
            author_score = author_prefs.get(item.author, 0.0)
        
        # Time decay factor (newer content gets higher score)
        time_factor = 1.0
        if item.published_at:
            hours_old = (datetime.utcnow() - item.published_at).total_seconds() / 3600
            time_factor = max(0.1, 1.0 - (hours_old / 168))  # Decay over 1 week
        
        # Engagement factor
        engagement_factor = min(2.0, 1.0 + item.engagement_score / 10.0)
        
        # Combine all factors
        final_score = (
            base_score * 0.3 +           # Base importance
            topic_score * 0.4 +          # Topic relevance
            source_score * 0.2 +         # Source preference
            author_score * 0.1           # Author preference
        ) * time_factor * engagement_factor
        
        # Clamp to [0, 1] range
        return max(0.0, min(1.0, final_score))
    
    def _get_score_factors(
        self,
        item: Item,
        topic_prefs: Dict[str, float],
        source_prefs: Dict[str, float], 
        author_prefs: Dict[str, float]
    ) -> Dict[str, Any]:
        """Get detailed scoring factors for debugging"""
        return {
            "base_importance": item.importance_score,
            "topic_match": any(
                topic_prefs.get(topic_data.get("name", ""), 0) > 0
                for topic_data in item.topics
                if isinstance(topic_data, dict)
            ),
            "source_preference": source_prefs.get(str(item.source_id), 0.0),
            "author_preference": author_prefs.get(item.author or "", 0.0),
            "engagement_score": item.engagement_score,
            "is_recent": item.is_recent
        }
    
    async def update_preferences_from_feedback(
        self,
        user_id: int,
        item: Item,
        feedback_type: str
    ):
        """Update user preferences based on feedback"""
        # Determine if feedback is positive or negative
        is_positive = feedback_type in ["like", "save", "click"]
        weight = 1.0 if is_positive else -0.5
        
        # Update topic preferences
        if item.topics:
            for topic_data in item.topics:
                if isinstance(topic_data, dict) and "name" in topic_data:
                    await self._update_preference(
                        user_id, "topic", topic_data["name"], weight
                    )
        
        # Update source preference
        await self._update_preference(
            user_id, "source", str(item.source_id), weight
        )
        
        # Update author preference
        if item.author:
            await self._update_preference(
                user_id, "author", item.author, weight * 0.5  # Lower weight for authors
            )
        
        logger.info(
            "Preferences updated from feedback",
            user_id=user_id,
            item_id=item.id,
            feedback_type=feedback_type
        )
    
    async def _update_preference(
        self,
        user_id: int,
        preference_type: str,
        preference_key: str,
        weight: float
    ):
        """Update or create a user preference"""
        # Try to get existing preference
        query = select(UserPreference).where(
            and_(
                UserPreference.user_id == user_id,
                UserPreference.preference_type == preference_type,
                UserPreference.preference_key == preference_key
            )
        )
        
        result = await self.db.execute(query)
        preference = result.scalar_one_or_none()
        
        if preference:
            # Update existing preference
            if weight > 0:
                preference.add_positive_interaction(abs(weight))
            else:
                preference.add_negative_interaction(abs(weight))
        else:
            # Create new preference
            preference = UserPreference(
                user_id=user_id,
                preference_type=preference_type,
                preference_key=preference_key,
                score=weight * 0.1,  # Start with small initial score
                positive_interactions=1 if weight > 0 else 0,
                negative_interactions=1 if weight < 0 else 0
            )
            self.db.add(preference)
        
        await self.db.commit()