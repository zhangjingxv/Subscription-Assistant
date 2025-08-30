"""
Collections management routes
"""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.database import get_db
from app.core.exceptions import NotFoundException
from app.models.user import User
from app.models.collection import Collection
from app.routers.auth import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_collections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's collections"""
    query = select(Collection).where(Collection.user_id == current_user.id)
    result = await db.execute(query)
    collections = result.scalars().all()
    
    return [
        {
            "id": collection.id,
            "name": collection.name,
            "description": collection.description,
            "item_count": collection.item_count,
            "is_default": collection.is_default,
            "created_at": collection.created_at
        }
        for collection in collections
    ]


@router.post("/")
async def create_collection(
    name: str,
    description: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new collection"""
    collection = Collection(
        name=name,
        description=description,
        user_id=current_user.id
    )
    
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    
    logger.info("Collection created", collection_id=collection.id, user_id=current_user.id)
    
    return {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description,
        "message": "Collection created successfully"
    }