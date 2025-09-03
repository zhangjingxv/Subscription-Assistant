"""
Simple RSS feed parser
Does one thing: parse RSS feeds
"""

import hashlib
from datetime import datetime
from typing import List, Optional

import feedparser
import httpx
from pydantic import BaseModel


class FeedItem(BaseModel):
    """Parsed feed item"""
    title: str
    link: str
    description: Optional[str] = None
    published: Optional[datetime] = None
    guid: Optional[str] = None
    
    def generate_hash(self) -> str:
        """Generate unique hash for deduplication"""
        content = f"{self.title}{self.link}"
        return hashlib.sha256(content.encode()).hexdigest()


class RSSParser:
    """Simple RSS feed parser"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    async def fetch_feed(self, url: str) -> List[FeedItem]:
        """Fetch and parse RSS feed"""
        try:
            # Fetch feed content
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout)
                response.raise_for_status()
            
            # Parse feed
            feed = feedparser.parse(response.text)
            
            # Convert to FeedItem objects
            items = []
            for entry in feed.entries:
                item = FeedItem(
                    title=entry.get('title', 'No title'),
                    link=entry.get('link', ''),
                    description=entry.get('summary', ''),
                    published=self._parse_date(entry.get('published_parsed')),
                    guid=entry.get('id', '')
                )
                items.append(item)
            
            return items
            
        except Exception as e:
            print(f"Error fetching feed {url}: {e}")
            return []
    
    def _parse_date(self, date_tuple) -> Optional[datetime]:
        """Parse date from feed"""
        if date_tuple:
            try:
                return datetime(*date_tuple[:6])
            except:
                pass
        return None


# Simple singleton instance
rss_parser = RSSParser()