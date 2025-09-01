"""
Content fetching service for AttentionSync
Handles fetching content from various sources (RSS, web pages, etc.)
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from readability import Document
import structlog

from app.core.config import get_settings
from app.models.source import Source, SourceType
from app.models.item import Item
from app.core.exception_handler import (
    exception_handler, safe_background_task, 
    ValidationException, ResourceException
)

logger = structlog.get_logger()


class ContentFetcher:
    """Service for fetching content from various sources"""
    
    def __init__(self):
        self.settings = get_settings()
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "User-Agent": "AttentionSync/1.0 (+https://github.com/attentionsync/attentionsync)"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_source_content(self, source: Source) -> List[Dict[str, Any]]:
        """Fetch content from a source based on its type"""
        try:
            if source.source_type == SourceType.RSS:
                return await self._fetch_rss_content(source)
            elif source.source_type == SourceType.WEBPAGE:
                return await self._fetch_webpage_content(source)
            elif source.source_type == SourceType.VIDEO:
                return await self._fetch_video_content(source)
            else:
                logger.warning("Unsupported source type", source_type=source.source_type)
                return []
                
        except Exception as e:
            logger.error(
                "Failed to fetch source content",
                source_id=source.id,
                source_type=source.source_type,
                error=str(e)
            )
            source.record_error(str(e))
            return []
    
    async def _fetch_rss_content(self, source: Source) -> List[Dict[str, Any]]:
        """Fetch content from RSS feed"""
        try:
            async with self.session.get(source.url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                feed_content = await response.text()
            
            # Parse RSS feed
            feed = feedparser.parse(feed_content)
            
            if feed.bozo:
                logger.warning("RSS feed has parsing errors", source_id=source.id)
            
            items = []
            for entry in feed.entries[:50]:  # Limit to 50 most recent items
                item_data = {
                    "title": entry.get("title", "Untitled"),
                    "content": self._extract_content_from_entry(entry),
                    "url": entry.get("link", ""),
                    "author": entry.get("author", ""),
                    "published_at": self._parse_published_date(entry),
                    "source_id": source.id
                }
                
                # Skip items without URL
                if not item_data["url"]:
                    continue
                
                items.append(item_data)
            
            logger.info(
                "RSS content fetched successfully",
                source_id=source.id,
                items_count=len(items)
            )
            
            source.record_success()
            return items
            
        except Exception as e:
            logger.error("RSS fetch failed", source_id=source.id, error=str(e))
            source.record_error(str(e))
            return []
    
    async def _fetch_webpage_content(self, source: Source) -> List[Dict[str, Any]]:
        """Fetch content from a single webpage"""
        try:
            async with self.session.get(source.url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                html_content = await response.text()
            
            # Extract readable content using readability
            doc = Document(html_content)
            
            # Parse with BeautifulSoup for additional metadata
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = doc.title() or ""
            if not title and soup.title:
                title = soup.title.get_text().strip()
            
            # Extract author from meta tags
            author = ""
            author_meta = soup.find("meta", {"name": "author"}) or soup.find("meta", {"property": "article:author"})
            if author_meta:
                author = author_meta.get("content", "")
            
            # Extract published date
            published_at = None
            date_meta = soup.find("meta", {"property": "article:published_time"})
            if date_meta:
                try:
                    published_at = datetime.fromisoformat(date_meta.get("content", "").replace("Z", "+00:00"))
                except:
                    pass
            
            item_data = {
                "title": title,
                "content": doc.summary(),
                "url": source.url,
                "author": author,
                "published_at": published_at or datetime.utcnow(),
                "source_id": source.id
            }
            
            logger.info("Webpage content fetched successfully", source_id=source.id)
            source.record_success()
            
            return [item_data]
            
        except Exception as e:
            logger.error("Webpage fetch failed", source_id=source.id, error=str(e))
            source.record_error(str(e))
            return []
    
    async def _fetch_video_content(self, source: Source) -> List[Dict[str, Any]]:
        """Fetch video content (placeholder for video processing)"""
        # This would integrate with video processing services
        # For now, just extract basic metadata
        
        try:
            platform = source.get_config("platform", "youtube")
            
            if platform == "youtube":
                return await self._fetch_youtube_metadata(source)
            elif platform == "bilibili":
                return await self._fetch_bilibili_metadata(source)
            else:
                logger.warning("Unsupported video platform", platform=platform)
                return []
                
        except Exception as e:
            logger.error("Video fetch failed", source_id=source.id, error=str(e))
            source.record_error(str(e))
            return []
    
    async def _fetch_youtube_metadata(self, source: Source) -> List[Dict[str, Any]]:
        """Fetch YouTube video metadata"""
        # This is a placeholder - would need YouTube API integration
        # For MVP, we'll just extract basic info from the URL
        
        try:
            async with self.session.get(source.url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title from page title
                title_tag = soup.find("title")
                title = title_tag.get_text() if title_tag else "YouTube Video"
                
                # Extract description from meta tag
                desc_meta = soup.find("meta", {"name": "description"})
                description = desc_meta.get("content", "") if desc_meta else ""
                
                item_data = {
                    "title": title,
                    "content": description,
                    "url": source.url,
                    "author": "YouTube",
                    "published_at": datetime.utcnow(),
                    "source_id": source.id
                }
                
                source.record_success()
                return [item_data]
                
        except Exception as e:
            logger.error("YouTube metadata fetch failed", source_id=source.id, error=str(e))
            source.record_error(str(e))
            return []
    
    async def _fetch_bilibili_metadata(self, source: Source) -> List[Dict[str, Any]]:
        """Fetch Bilibili video metadata"""
        # Placeholder for Bilibili integration
        logger.info("Bilibili integration not yet implemented", source_id=source.id)
        return []
    
    def _extract_content_from_entry(self, entry) -> str:
        """Extract content from RSS entry"""
        # Try different content fields in order of preference
        content_fields = [
            "content", "summary", "description"
        ]
        
        for field in content_fields:
            if hasattr(entry, field):
                content = getattr(entry, field)
                if isinstance(content, list) and len(content) > 0:
                    # Handle structured content
                    content = content[0].get("value", "")
                elif isinstance(content, str):
                    pass
                else:
                    content = str(content)
                
                if content and len(content.strip()) > 10:
                    # Clean HTML tags
                    soup = BeautifulSoup(content, 'html.parser')
                    return soup.get_text().strip()
        
        return ""
    
    def _parse_published_date(self, entry) -> Optional[datetime]:
        """Parse published date from RSS entry"""
        date_fields = ["published", "updated", "created"]
        
        for field in date_fields:
            if hasattr(entry, field + "_parsed"):
                try:
                    time_struct = getattr(entry, field + "_parsed")
                    if time_struct:
                        return datetime(*time_struct[:6])
                except:
                    continue
        
        return None