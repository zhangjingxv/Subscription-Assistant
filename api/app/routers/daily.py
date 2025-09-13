"""
Daily digest and 3-minute reading routes
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import selectinload
import structlog

from app.core.db import get_db
from app.models.user import User
from app.models.item import Item
from app.models.source import Source
from app.routers.auth import get_current_user
from app.schemas.item import ItemSummary
from app.services.personalization import PersonalizationService

logger = structlog.get_logger()
router = APIRouter()


@router.get("/digest", response_model=List[ItemSummary])
async def get_daily_digest(
    date: datetime = Query(None, description="Date for digest (defaults to today)"),
    limit: int = Query(10, ge=1, le=20, description="Number of items in digest"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get personalized daily digest - the core 3-minute reading feature"""
    if not date:
        date = datetime.utcnow().date()
    
    # Get items from the last 24 hours from user's sources
    start_time = datetime.combine(date, datetime.min.time())
    end_time = start_time + timedelta(days=1)
    
    query = select(Item).join(Source).where(
        and_(
            Source.user_id == current_user.id,
            Item.is_duplicate == False,
            Item.is_processed == True,
            Item.published_at >= start_time,
            Item.published_at < end_time
        )
    ).options(selectinload(Item.source))
    
    result = await db.execute(query)
    all_items = result.scalars().all()
    
    if not all_items:
        logger.info("No items found for daily digest", user_id=current_user.id, date=date)
        return []
    
    # Apply personalization scoring
    personalization_service = PersonalizationService(db)
    scored_items = await personalization_service.score_items_for_user(
        current_user.id, 
        all_items
    )
    
    # Sort by personalized score and take top items
    top_items = sorted(
        scored_items,
        key=lambda x: x["score"],
        reverse=True
    )[:limit]
    
    # Convert to response format
    digest_items = []
    for item_data in top_items:
        item = item_data["item"]
        digest_items.append(ItemSummary(
            id=item.id,
            title=item.title,
            summary=item.summary,
            url=item.url,
            author=item.author,
            published_at=item.published_at,
            importance_score=item.importance_score,
            topics=[topic["name"] for topic in item.topics if isinstance(topic, dict)],
            source_name=item.source.name
        ))
    
    logger.info(
        "Daily digest generated",
        user_id=current_user.id,
        date=date,
        total_items=len(all_items),
        digest_items=len(digest_items)
    )
    
    return digest_items


@router.get("/stats")
async def get_daily_stats(
    date: datetime = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily reading statistics"""
    if not date:
        date = datetime.utcnow().date()
    
    start_time = datetime.combine(date, datetime.min.time())
    end_time = start_time + timedelta(days=1)
    
    # Count items by various metrics
    base_query = select(func.count(Item.id)).join(Source).where(
        and_(
            Source.user_id == current_user.id,
            Item.published_at >= start_time,
            Item.published_at < end_time
        )
    )
    
    # Total items
    total_items = (await db.execute(base_query)).scalar()
    
    # Processed items
    processed_query = base_query.where(Item.is_processed == True)
    processed_items = (await db.execute(processed_query)).scalar()
    
    # High importance items
    high_importance_query = base_query.where(Item.importance_score >= 0.7)
    high_importance_items = (await db.execute(high_importance_query)).scalar()
    
    # Items with video/audio
    media_query = base_query.where(
        or_(Item.has_video == True, Item.has_audio == True)
    )
    media_items = (await db.execute(media_query)).scalar()
    
    return {
        "date": date,
        "total_items": total_items,
        "processed_items": processed_items,
        "high_importance_items": high_importance_items,
        "media_items": media_items,
        "processing_rate": processed_items / total_items if total_items > 0 else 0
    }


@router.post("/feedback")
async def record_digest_feedback(
    item_id: int,
    feedback_type: str = Query(..., regex="^(like|dislike|save|skip)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record user feedback on daily digest items for personalization"""
    # Verify item belongs to user
    query = select(Item).join(Source).where(
        Item.id == item_id,
        Source.user_id == current_user.id
    )
    
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise NotFoundError("Item not found")
    
    # Record interaction based on feedback type
    if feedback_type == "like":
        item.increment_click()
    elif feedback_type == "save":
        item.increment_click()
        # TODO: Add to default collection
    elif feedback_type == "skip":
        # Negative signal for personalization
        pass
    
    await db.commit()
    
    # Update user preferences (this would be handled by PersonalizationService)
    personalization_service = PersonalizationService(db)
    await personalization_service.update_preferences_from_feedback(
        current_user.id,
        item,
        feedback_type
    )
    
    logger.info(
        "Digest feedback recorded",
        user_id=current_user.id,
        item_id=item.id,
        feedback_type=feedback_type
    )
    
    return {"message": "Feedback recorded successfully"}