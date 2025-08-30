"""
Search and discovery routes
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
import structlog

from app.core.database import get_db
from app.models.user import User
from app.models.item import Item
from app.models.source import Source
from app.routers.auth import get_current_user
from app.schemas.item import ItemSummary

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[ItemSummary])
async def search_items(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    skip: int = Query(0, ge=0),
    source_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search items using full-text search"""
    # Base query - only items from user's sources
    query = select(Item).join(Source).where(
        Source.user_id == current_user.id,
        Item.is_duplicate == False
    )
    
    # Apply source filter if specified
    if source_id:
        query = query.where(Item.source_id == source_id)
    
    # Full-text search in title, content, and summary
    search_condition = or_(
        Item.title.ilike(f"%{q}%"),
        Item.content.ilike(f"%{q}%"),
        Item.summary.ilike(f"%{q}%"),
        Item.author.ilike(f"%{q}%")
    )
    
    query = query.where(search_condition)
    
    # Order by relevance (importance score) and recency
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
    
    logger.info(
        "Search performed",
        user_id=current_user.id,
        query=q,
        results_count=len(summaries)
    )
    
    return summaries


@router.get("/suggestions/topics")
async def get_topic_suggestions(
    q: str = Query("", description="Partial topic name for suggestions"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get topic suggestions for search autocomplete"""
    # Get recent items from user's sources
    query = select(Item).join(Source).where(
        Source.user_id == current_user.id,
        Item.is_duplicate == False,
        Item.published_at >= func.now() - func.interval('30 days')
    )
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Extract and filter topics
    topic_counts = {}
    for item in items:
        if item.topics:
            for topic_data in item.topics:
                if isinstance(topic_data, dict) and "name" in topic_data:
                    topic_name = topic_data["name"]
                    if q.lower() in topic_name.lower():
                        topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
    
    # Sort by frequency and return suggestions
    suggestions = sorted(
        topic_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [
        {"topic": topic, "count": count}
        for topic, count in suggestions
    ]


@router.get("/suggestions/sources")
async def get_source_suggestions(
    q: str = Query("", description="Search query for source recommendations"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get source recommendations based on user's interests"""
    # This would typically use a recommendation algorithm
    # For now, return popular sources that user hasn't added
    
    # Get user's existing sources
    user_sources_query = select(Source.url).where(Source.user_id == current_user.id)
    result = await db.execute(user_sources_query)
    user_source_urls = {row[0] for row in result.fetchall()}
    
    # Predefined popular sources (in production, this would be data-driven)
    popular_sources = [
        {
            "name": "Hacker News",
            "url": "https://news.ycombinator.com/rss",
            "type": "rss",
            "description": "Technology and startup news"
        },
        {
            "name": "36氪",
            "url": "https://36kr.com/feed",
            "type": "rss", 
            "description": "中文科技创业资讯"
        },
        {
            "name": "虎嗅网",
            "url": "https://www.huxiu.com/rss/0.xml",
            "type": "rss",
            "description": "商业科技资讯"
        },
        {
            "name": "少数派",
            "url": "https://sspai.com/feed",
            "type": "rss",
            "description": "数字生活指南"
        },
        {
            "name": "阮一峰的网络日志",
            "url": "http://www.ruanyifeng.com/blog/atom.xml",
            "type": "rss",
            "description": "技术博客"
        }
    ]
    
    # Filter out sources user already has
    recommendations = [
        source for source in popular_sources
        if source["url"] not in user_source_urls
    ]
    
    # Filter by search query if provided
    if q:
        recommendations = [
            source for source in recommendations
            if q.lower() in source["name"].lower() or q.lower() in source["description"].lower()
        ]
    
    return recommendations[:limit]