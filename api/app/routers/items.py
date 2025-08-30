"""
Items management routes
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload
import structlog

from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.item import Item
from app.models.source import Source
from app.routers.auth import get_current_user
from app.schemas.item import ItemResponse, ItemSummary, ItemFilter

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[ItemSummary])
async def list_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    source_id: int = Query(None),
    topic: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's items with filtering"""
    # Base query - only items from user's sources
    query = select(Item).join(Source).where(
        Source.user_id == current_user.id,
        Item.is_duplicate == False
    )
    
    # Apply filters
    if source_id:
        query = query.where(Item.source_id == source_id)
    
    if topic:
        # Search in topics JSON field
        query = query.where(Item.topics.contains([{"name": topic}]))
    
    # Order by importance and recency
    query = query.order_by(
        desc(Item.importance_score),
        desc(Item.published_at)
    ).offset(skip).limit(limit)
    
    # Execute query with source relationship loaded
    query = query.options(selectinload(Item.source))
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Convert to summary format
    summaries = []
    for item in items:
        summary = ItemSummary(
            id=item.id,
            title=item.title,
            summary=item.summary,
            url=item.url,
            author=item.author,
            published_at=item.published_at,
            importance_score=item.importance_score,
            topics=[topic["name"] for topic in item.topics if isinstance(topic, dict)],
            source_name=item.source.name
        )
        summaries.append(summary)
    
    return summaries


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific item"""
    query = select(Item).join(Source).where(
        Item.id == item_id,
        Source.user_id == current_user.id
    ).options(selectinload(Item.source))
    
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise NotFoundException("Item not found")
    
    # Increment view count
    item.increment_view()
    await db.commit()
    
    return ItemResponse.from_orm(item)


@router.post("/{item_id}/click")
async def record_click(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record user click on item"""
    query = select(Item).join(Source).where(
        Item.id == item_id,
        Source.user_id == current_user.id
    )
    
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise NotFoundException("Item not found")
    
    # Increment click count
    item.increment_click()
    await db.commit()
    
    logger.info("Item click recorded", item_id=item.id, user_id=current_user.id)
    
    return {"message": "Click recorded successfully"}


@router.post("/{item_id}/share")
async def record_share(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record user share of item"""
    query = select(Item).join(Source).where(
        Item.id == item_id,
        Source.user_id == current_user.id
    )
    
    result = await db.execute(query)
    item = result.scalar_one_or_none()
    
    if not item:
        raise NotFoundException("Item not found")
    
    # Increment share count
    item.increment_share()
    await db.commit()
    
    logger.info("Item share recorded", item_id=item.id, user_id=current_user.id)
    
    return {"message": "Share recorded successfully"}


@router.get("/trending/topics")
async def get_trending_topics(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get trending topics from user's items"""
    # Get recent items from user's sources
    query = select(Item).join(Source).where(
        Source.user_id == current_user.id,
        Item.is_duplicate == False,
        Item.published_at >= func.now() - func.interval('7 days')  # Last 7 days
    )
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Count topic frequencies
    topic_counts = {}
    for item in items:
        if item.topics:
            for topic_data in item.topics:
                if isinstance(topic_data, dict) and "name" in topic_data:
                    topic_name = topic_data["name"]
                    topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
    
    # Sort by frequency and return top topics
    trending_topics = sorted(
        topic_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [
        {"topic": topic, "count": count}
        for topic, count in trending_topics
    ]