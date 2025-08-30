"""
Sources management routes
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ValidationException
from app.models.user import User
from app.models.source import Source, SourceStatus
from app.routers.auth import get_current_user
from app.schemas.source import SourceCreate, SourceUpdate, SourceResponse, SourceStats

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[SourceResponse])
async def list_sources(
    skip: int = 0,
    limit: int = 100,
    status_filter: SourceStatus = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's information sources"""
    query = select(Source).where(Source.user_id == current_user.id)
    
    if status_filter:
        query = query.where(Source.status == status_filter)
    
    query = query.offset(skip).limit(limit).order_by(Source.created_at.desc())
    
    result = await db.execute(query)
    sources = result.scalars().all()
    
    return [SourceResponse.from_orm(source) for source in sources]


@router.post("/", response_model=SourceResponse)
async def create_source(
    source_data: SourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new information source"""
    # Check if source already exists for this user
    existing_query = select(Source).where(
        Source.user_id == current_user.id,
        Source.url == str(source_data.url)
    )
    result = await db.execute(existing_query)
    existing_source = result.scalar_one_or_none()
    
    if existing_source:
        raise ValidationException("Source with this URL already exists")
    
    # Create new source
    source = Source(
        name=source_data.name,
        description=source_data.description,
        url=str(source_data.url),
        source_type=source_data.source_type,
        fetch_interval_minutes=source_data.fetch_interval_minutes,
        config=source_data.config,
        headers=source_data.headers,
        user_id=current_user.id
    )
    
    db.add(source)
    await db.commit()
    await db.refresh(source)
    
    logger.info(
        "Source created successfully",
        source_id=source.id,
        user_id=current_user.id,
        source_type=source.source_type,
        url=source.url
    )
    
    return SourceResponse.from_orm(source)


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific source"""
    query = select(Source).where(
        Source.id == source_id,
        Source.user_id == current_user.id
    )
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise NotFoundException("Source not found")
    
    return SourceResponse.from_orm(source)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    source_data: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a source"""
    query = select(Source).where(
        Source.id == source_id,
        Source.user_id == current_user.id
    )
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise NotFoundException("Source not found")
    
    # Update fields
    update_data = source_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(source, field):
            setattr(source, field, value)
    
    await db.commit()
    await db.refresh(source)
    
    logger.info("Source updated successfully", source_id=source.id, user_id=current_user.id)
    
    return SourceResponse.from_orm(source)


@router.delete("/{source_id}")
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a source"""
    query = select(Source).where(
        Source.id == source_id,
        Source.user_id == current_user.id
    )
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise NotFoundException("Source not found")
    
    await db.delete(source)
    await db.commit()
    
    logger.info("Source deleted successfully", source_id=source.id, user_id=current_user.id)
    
    return {"message": "Source deleted successfully"}


@router.post("/{source_id}/pause")
async def pause_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Pause a source"""
    query = select(Source).where(
        Source.id == source_id,
        Source.user_id == current_user.id
    )
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise NotFoundException("Source not found")
    
    source.status = SourceStatus.PAUSED
    await db.commit()
    
    logger.info("Source paused", source_id=source.id, user_id=current_user.id)
    
    return {"message": "Source paused successfully"}


@router.post("/{source_id}/resume")
async def resume_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resume a paused source"""
    query = select(Source).where(
        Source.id == source_id,
        Source.user_id == current_user.id
    )
    result = await db.execute(query)
    source = result.scalar_one_or_none()
    
    if not source:
        raise NotFoundException("Source not found")
    
    source.status = SourceStatus.ACTIVE
    await db.commit()
    
    logger.info("Source resumed", source_id=source.id, user_id=current_user.id)
    
    return {"message": "Source resumed successfully"}


@router.get("/stats/overview", response_model=SourceStats)
async def get_source_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get source statistics overview"""
    # Count sources by status
    total_query = select(func.count(Source.id)).where(Source.user_id == current_user.id)
    active_query = select(func.count(Source.id)).where(
        Source.user_id == current_user.id,
        Source.status == SourceStatus.ACTIVE
    )
    paused_query = select(func.count(Source.id)).where(
        Source.user_id == current_user.id,
        Source.status == SourceStatus.PAUSED
    )
    error_query = select(func.count(Source.id)).where(
        Source.user_id == current_user.id,
        Source.status == SourceStatus.ERROR
    )
    
    total_sources = (await db.execute(total_query)).scalar()
    active_sources = (await db.execute(active_query)).scalar()
    paused_sources = (await db.execute(paused_query)).scalar()
    error_sources = (await db.execute(error_query)).scalar()
    
    # Calculate average success rate
    sources_query = select(Source).where(Source.user_id == current_user.id)
    result = await db.execute(sources_query)
    sources = result.scalars().all()
    
    if sources:
        avg_success_rate = sum(source.success_rate for source in sources) / len(sources)
    else:
        avg_success_rate = 0.0
    
    return SourceStats(
        total_sources=total_sources,
        active_sources=active_sources,
        paused_sources=paused_sources,
        error_sources=error_sources,
        total_items_today=0,  # TODO: Implement daily item count
        avg_success_rate=avg_success_rate
    )