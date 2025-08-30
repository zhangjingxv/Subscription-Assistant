"""
Content processing service for AttentionSync
Handles AI summarization, deduplication, and content analysis
"""

import hashlib
import re
from typing import List, Optional, Dict, Any
import asyncio

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
import structlog

from app.core.config import get_settings
from app.models.item import Item

logger = structlog.get_logger()


class ContentProcessor:
    """Service for processing and analyzing content"""
    
    def __init__(self):
        self.settings = get_settings()
        self.anthropic_client = None
        self.openai_client = None
        
        # Initialize AI clients
        if self.settings.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=self.settings.anthropic_api_key)
        
        if self.settings.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
    
    async def process_item(self, item: Item) -> Item:
        """Process a single item through the full pipeline"""
        try:
            # 1. Generate content hash for deduplication
            item.content_hash = self._generate_content_hash(item)
            
            # 2. Generate summary
            if item.content and not item.summary:
                item.summary = await self._generate_summary(item.content, item.title)
            
            # 3. Extract topics and entities
            if item.content:
                topics, entities = await self._extract_topics_and_entities(item.content)
                item.topics = topics
                item.entities = entities
            
            # 4. Calculate importance score
            item.importance_score = self._calculate_importance_score(item)
            
            # 5. Detect media content
            self._detect_media_content(item)
            
            item.is_processed = True
            
            logger.info("Item processed successfully", item_id=item.id)
            
        except Exception as e:
            logger.error("Failed to process item", item_id=item.id, error=str(e))
            item.is_processed = False
        
        return item
    
    def _generate_content_hash(self, item: Item) -> str:
        """Generate hash for content deduplication"""
        # Combine title and first 500 chars of content
        content_for_hash = item.title
        if item.content:
            content_for_hash += item.content[:500]
        
        # Clean and normalize text
        normalized = re.sub(r'\s+', ' ', content_for_hash.lower().strip())
        
        # Generate SHA-256 hash
        return hashlib.sha256(normalized.encode()).hexdigest()
    
    async def _generate_summary(self, content: str, title: str) -> Optional[str]:
        """Generate AI summary of content"""
        try:
            # Prepare content for summarization
            text_to_summarize = f"标题：{title}\n\n内容：{content[:3000]}"  # Limit content length
            
            # Try Claude first, then OpenAI as fallback
            if self.anthropic_client:
                summary = await self._summarize_with_claude(text_to_summarize)
                if summary:
                    return summary
            
            if self.openai_client:
                summary = await self._summarize_with_openai(text_to_summarize)
                if summary:
                    return summary
            
            logger.warning("No AI service available for summarization")
            return None
            
        except Exception as e:
            logger.error("Failed to generate summary", error=str(e))
            return None
    
    async def _summarize_with_claude(self, content: str) -> Optional[str]:
        """Generate summary using Claude"""
        try:
            prompt = f"""请为以下内容生成一个简洁的摘要，要求：
1. 控制在{self.settings.summary_max_length}字以内
2. 突出关键信息和要点
3. 使用清晰易懂的语言
4. 保持客观中性的语调

内容：
{content}

摘要："""

            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            summary = response.content[0].text.strip()
            
            # Ensure summary is within length limit
            if len(summary) > self.settings.summary_max_length:
                summary = summary[:self.settings.summary_max_length-3] + "..."
            
            return summary
            
        except Exception as e:
            logger.error("Claude summarization failed", error=str(e))
            return None
    
    async def _summarize_with_openai(self, content: str) -> Optional[str]:
        """Generate summary using OpenAI"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"你是一个专业的内容摘要助手。请为用户提供的内容生成简洁的摘要，控制在{self.settings.summary_max_length}字以内，突出关键信息。"
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Ensure summary is within length limit
            if len(summary) > self.settings.summary_max_length:
                summary = summary[:self.settings.summary_max_length-3] + "..."
            
            return summary
            
        except Exception as e:
            logger.error("OpenAI summarization failed", error=str(e))
            return None
    
    async def _extract_topics_and_entities(self, content: str) -> tuple[List[Dict], List[Dict]]:
        """Extract topics and named entities from content"""
        topics = []
        entities = []
        
        try:
            # Simple keyword-based topic extraction (can be enhanced with ML models)
            topic_keywords = {
                "人工智能": ["AI", "人工智能", "机器学习", "深度学习", "神经网络"],
                "区块链": ["区块链", "比特币", "以太坊", "NFT", "DeFi"],
                "创业": ["创业", "融资", "投资", "IPO", "独角兽"],
                "科技": ["科技", "技术", "软件", "硬件", "互联网"],
                "金融": ["金融", "银行", "股票", "基金", "保险"]
            }
            
            content_lower = content.lower()
            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in content_lower:
                        topics.append({
                            "name": topic,
                            "confidence": 0.8,
                            "keyword": keyword
                        })
                        break
            
            # Simple entity extraction (company names, people)
            # This is a basic implementation - can be enhanced with NER models
            company_patterns = [
                r'(苹果|微软|谷歌|亚马逊|特斯拉|阿里巴巴|腾讯|百度|字节跳动)(?:公司)?',
                r'(Apple|Microsoft|Google|Amazon|Tesla|Meta|Netflix|OpenAI)'
            ]
            
            for pattern in company_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group(1)
                    entities.append({
                        "name": entity_name,
                        "type": "company",
                        "confidence": 0.9
                    })
            
        except Exception as e:
            logger.error("Failed to extract topics and entities", error=str(e))
        
        return topics, entities
    
    def _calculate_importance_score(self, item: Item) -> float:
        """Calculate importance score for an item"""
        score = 0.5  # Base score
        
        # Title length factor (longer titles often more important)
        if item.title:
            title_length_factor = min(1.0, len(item.title) / 100)
            score += title_length_factor * 0.1
        
        # Content length factor
        if item.content:
            content_length_factor = min(1.0, len(item.content) / 2000)
            score += content_length_factor * 0.1
        
        # Recency factor (recent content is more important)
        if item.published_at:
            hours_old = (datetime.utcnow() - item.published_at).total_seconds() / 3600
            if hours_old < 6:  # Very recent
                score += 0.2
            elif hours_old < 24:  # Recent
                score += 0.1
        
        # Media content bonus
        if item.has_video or item.has_audio:
            score += 0.1
        
        # Topic relevance bonus
        if item.topics and len(item.topics) > 0:
            score += 0.1
        
        # Clamp to [0, 1] range
        return max(0.0, min(1.0, score))
    
    def _detect_media_content(self, item: Item):
        """Detect if item contains media content"""
        if not item.content:
            return
        
        content_lower = item.content.lower()
        
        # Video detection
        video_indicators = [
            "youtube.com", "youtu.be", "bilibili.com", "b23.tv",
            "视频", "播放", "观看", "video"
        ]
        item.has_video = any(indicator in content_lower for indicator in video_indicators)
        
        # Audio detection
        audio_indicators = [
            "podcast", "播客", "音频", "audio", "听", "收听"
        ]
        item.has_audio = any(indicator in content_lower for indicator in audio_indicators)
        
        # Image detection
        image_indicators = [
            ".jpg", ".png", ".gif", ".webp", "图片", "图像", "image"
        ]
        item.has_images = any(indicator in content_lower for indicator in image_indicators)
    
    async def find_duplicates(self, item: Item, existing_items: List[Item]) -> Optional[Item]:
        """Find duplicate items based on content hash"""
        if not item.content_hash:
            return None
        
        for existing_item in existing_items:
            if (existing_item.content_hash == item.content_hash and 
                existing_item.id != item.id):
                return existing_item
        
        return None
    
    async def deduplicate_items(self, items: List[Item]) -> List[Item]:
        """Remove duplicate items from a list"""
        seen_hashes = set()
        unique_items = []
        
        for item in items:
            if item.content_hash and item.content_hash in seen_hashes:
                item.is_duplicate = True
                continue
            
            if item.content_hash:
                seen_hashes.add(item.content_hash)
            
            unique_items.append(item)
        
        return unique_items