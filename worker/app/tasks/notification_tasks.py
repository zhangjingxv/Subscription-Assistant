"""
Notification and alert tasks
"""

from datetime import datetime
from typing import List

import structlog

from app.celery_app import celery_app
from app.core.database import init_sync_db, get_sync_db

# Import from API
import sys
import os
api_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "api")
sys.path.insert(0, api_path)

from app.models.user import User
from app.models.item import Item

logger = structlog.get_logger()


@celery_app.task
def send_daily_digest_notification(user_id: int):
    """Send daily digest notification to user"""
    try:
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            db.close()
            return
        
        # Check user notification preferences
        notifications_enabled = user.get_setting("notifications_enabled", True)
        if not notifications_enabled:
            db.close()
            logger.info("Notifications disabled for user", user_id=user_id)
            return
        
        # Get digest time preference
        digest_time = user.get_setting("daily_digest_time", "07:00")
        
        # This would integrate with notification services (email, push, etc.)
        logger.info(
            "Daily digest notification sent",
            user_id=user_id,
            email=user.email,
            digest_time=digest_time
        )
        
        db.close()
        
        return {
            "status": "sent",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to send notification", user_id=user_id, error=str(e))
        raise


@celery_app.task
def send_important_item_alert(item_id: int):
    """Send alert for high-importance items"""
    try:
        init_sync_db()
        db_gen = get_sync_db()
        db = next(db_gen)
        
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            db.close()
            return
        
        # Only send alerts for very high importance items
        if item.importance_score < 0.9:
            db.close()
            return
        
        # Get source owner
        source = item.source
        user = source.user
        
        if not user.is_active:
            db.close()
            return
        
        # Check if user wants important item alerts
        alerts_enabled = user.get_setting("important_alerts_enabled", True)
        if not alerts_enabled:
            db.close()
            return
        
        logger.info(
            "Important item alert sent",
            user_id=user.id,
            item_id=item.id,
            importance_score=item.importance_score
        )
        
        db.close()
        
        return {
            "status": "sent",
            "item_id": item_id,
            "user_id": user.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to send important item alert", item_id=item_id, error=str(e))
        raise