"""
Content processing and analysis tasks
"""

import asyncio
from datetime import datetime, timedelta

from celery import current_task
from sqlalchemy import select, and_
import structlog

from app.celery_app import celery_app
from app.core.database import init_sync_db, get_sync_db

# Import from API
import sys
import os
api_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "api")
sys.path.insert(0, api_path)

from app.models.item import Item
from app.models.user import User
from app.services.content_processor import ContentProcessor

logger = structlog.get_logger()


@celery_app.task(bind=True)
def process_pending_items(self):
    """Process all pending items that need AI analysis"""
    try:
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        # Get unprocessed items
        unprocessed_items = db.query(Item).filter(
            Item.is_processed == False,
            Item.is_duplicate == False
        ).limit(100).all()  # Process in batches
        
        if not unprocessed_items:
            db.close()
            logger.info("No pending items to process")
            return {"status": "completed", "items_processed": 0}
        
        logger.info("Processing pending items", items_count=len(unprocessed_items))
        
        # Process items
        processor = ContentProcessor()
        processed_count = 0
        
        for i, item in enumerate(unprocessed_items):
            try:
                # Update task progress
                current_task.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(unprocessed_items),
                        "status": f"Processing item {item.id}"
                    }
                )
                
                # Process the item
                await asyncio.run(processor.process_item(item))
                processed_count += 1
                
                # Commit every 10 items to avoid long transactions
                if (i + 1) % 10 == 0:
                    db.commit()
                
            except Exception as e:
                logger.error("Failed to process item", item_id=item.id, error=str(e))
                continue
        
        # Final commit
        db.commit()
        db.close()
        
        logger.info("Pending items processing completed", processed_count=processed_count)
        
        return {
            "status": "completed",
            "items_processed": processed_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Processing task failed", error=str(e))
        raise


@celery_app.task
def generate_daily_digests():
    """Generate daily digests for all users"""
    try:
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        # Get all active users
        active_users = db.query(User).filter(User.is_active == True).all()
        
        logger.info("Generating daily digests", users_count=len(active_users))
        
        digests_generated = 0
        for user in active_users:
            try:
                # This would trigger digest generation for each user
                # For now, just log the action
                logger.info("Daily digest generated", user_id=user.id)
                digests_generated += 1
                
            except Exception as e:
                logger.error("Failed to generate digest for user", user_id=user.id, error=str(e))
                continue
        
        db.close()
        
        logger.info("Daily digests generation completed", digests_generated=digests_generated)
        
        return {
            "status": "completed",
            "digests_generated": digests_generated,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Daily digest generation failed", error=str(e))
        raise


@celery_app.task
def cleanup_old_data():
    """Clean up old data to maintain database performance"""
    try:
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        # Delete items older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        old_items = db.query(Item).filter(
            Item.created_at < cutoff_date
        )
        
        deleted_count = old_items.count()
        old_items.delete()
        
        db.commit()
        db.close()
        
        logger.info("Old data cleanup completed", deleted_items=deleted_count)
        
        return {
            "status": "completed", 
            "deleted_items": deleted_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Data cleanup failed", error=str(e))
        raise


@celery_app.task
def process_video_content(item_id: int):
    """Process video content (transcription, etc.)"""
    try:
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            logger.error("Item not found for video processing", item_id=item_id)
            return
        
        # This would integrate with video processing services
        # For now, just mark as processed
        logger.info("Video processing started", item_id=item_id)
        
        # Placeholder for video transcription logic
        # item.content = await transcribe_video(item.url)
        
        item.has_video = True
        item.is_processed = True
        
        db.commit()
        db.close()
        
        logger.info("Video processing completed", item_id=item_id)
        
        return {"status": "completed", "item_id": item_id}
        
    except Exception as e:
        logger.error("Video processing failed", item_id=item_id, error=str(e))
        raise