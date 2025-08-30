"""
Content fetching and processing tasks
"""

import asyncio
from datetime import datetime, timedelta
from typing import List

from celery import current_task
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
import structlog

from app.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import init_sync_db, get_sync_db

# Import models and services from API
import sys
import os
api_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "api")
sys.path.insert(0, api_path)

from app.models.source import Source, SourceStatus
from app.models.item import Item
from app.services.content_fetcher import ContentFetcher
from app.services.content_processor import ContentProcessor

logger = structlog.get_logger()


@celery_app.task(bind=True)
def fetch_all_sources(self):
    """Fetch content from all active sources"""
    try:
        # Initialize database connection for worker
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        # Get all active sources
        active_sources = db.query(Source).filter(
            Source.status == SourceStatus.ACTIVE
        ).all()
        
        logger.info("Starting content fetch", sources_count=len(active_sources))
        
        # Process sources in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(active_sources), batch_size):
            batch = active_sources[i:i + batch_size]
            
            # Update task progress
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "current": i,
                    "total": len(active_sources),
                    "status": f"Processing batch {i//batch_size + 1}"
                }
            )
            
            # Process batch asynchronously
            asyncio.run(process_source_batch(batch, db))
        
        db.close()
        
        logger.info("Content fetch completed", sources_count=len(active_sources))
        
        return {
            "status": "completed",
            "sources_processed": len(active_sources),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Content fetch failed", error=str(e))
        raise


async def process_source_batch(sources: List[Source], db):
    """Process a batch of sources concurrently"""
    async with ContentFetcher() as fetcher:
        tasks = []
        for source in sources:
            task = process_single_source(fetcher, source, db)
            tasks.append(task)
        
        # Process all sources in batch concurrently
        await asyncio.gather(*tasks, return_exceptions=True)


async def process_single_source(fetcher: ContentFetcher, source: Source, db):
    """Process a single source"""
    try:
        # Check if enough time has passed since last fetch
        if source.last_fetched_at:
            time_since_last = datetime.utcnow() - source.last_fetched_at
            if time_since_last.total_seconds() < source.fetch_interval_minutes * 60:
                logger.debug("Skipping source - too soon", source_id=source.id)
                return
        
        # Fetch content
        content_items = await fetcher.fetch_source_content(source)
        
        if not content_items:
            logger.info("No new content found", source_id=source.id)
            return
        
        # Save items to database
        new_items_count = 0
        for item_data in content_items:
            # Check if item already exists
            existing_item = db.query(Item).filter(
                Item.url == item_data["url"],
                Item.source_id == source.id
            ).first()
            
            if existing_item:
                continue  # Skip existing items
            
            # Create new item
            item = Item(**item_data)
            db.add(item)
            new_items_count += 1
        
        # Update source statistics
        source.total_items += new_items_count
        db.commit()
        
        logger.info(
            "Source processed successfully",
            source_id=source.id,
            new_items=new_items_count
        )
        
        # Queue processing tasks for new items
        if new_items_count > 0:
            process_source_items.delay(source.id)
        
    except Exception as e:
        logger.error("Failed to process source", source_id=source.id, error=str(e))
        source.record_error(str(e))
        db.commit()


@celery_app.task
def process_source_items(source_id: int):
    """Process unprocessed items from a specific source"""
    try:
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        # Get unprocessed items from this source
        unprocessed_items = db.query(Item).filter(
            Item.source_id == source_id,
            Item.is_processed == False
        ).limit(50).all()  # Process in batches
        
        if not unprocessed_items:
            db.close()
            return
        
        # Process items
        processor = ContentProcessor()
        for item in unprocessed_items:
            asyncio.run(processor.process_item(item))
        
        db.commit()
        db.close()
        
        logger.info(
            "Items processed",
            source_id=source_id,
            items_count=len(unprocessed_items)
        )
        
    except Exception as e:
        logger.error("Failed to process source items", source_id=source_id, error=str(e))
        raise


@celery_app.task
def health_check():
    """Health check task to verify worker is functioning"""
    try:
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        # Simple database connectivity check
        source_count = db.query(Source).count()
        
        db.close()
        
        logger.info("Health check passed", source_count=source_count)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "source_count": source_count
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise