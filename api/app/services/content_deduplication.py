"""
内容去重服务
使用多种算法确保内容的唯一性
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from collections import defaultdict
import asyncio

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.item import Item
from app.core.cache import cache_manager

logger = structlog.get_logger()


class ContentDeduplicator:
    """内容去重器"""
    
    def __init__(self):
        self.similarity_threshold = 0.85  # 相似度阈值
        self.title_similarity_threshold = 0.9  # 标题相似度阈值
        self.hash_cache = {}  # 内容哈希缓存
        
    def generate_content_hash(self, content: str) -> str:
        """生成内容指纹哈希"""
        if not content:
            return ""
        
        # 清理内容
        cleaned = self._clean_content(content)
        
        # 生成 SHA-256 哈希
        return hashlib.sha256(cleaned.encode('utf-8')).hexdigest()
    
    def generate_fuzzy_hash(self, content: str) -> str:
        """生成模糊哈希（用于相似内容检测）"""
        if not content:
            return ""
        
        # 提取关键特征
        features = self._extract_content_features(content)
        feature_string = ''.join(features)
        
        # 生成较短的哈希用于快速比较
        return hashlib.md5(feature_string.encode('utf-8')).hexdigest()[:16]
    
    def _clean_content(self, content: str) -> str:
        """清理内容，移除无关字符"""
        # 移除 HTML 标签
        content = re.sub(r'<[^>]+>', '', content)
        
        # 移除多余的空白字符
        content = re.sub(r'\s+', ' ', content)
        
        # 移除特殊字符和标点（保留中文字符）
        content = re.sub(r'[^\w\u4e00-\u9fff\s]', '', content)
        
        # 转换为小写并去除首尾空格
        return content.lower().strip()
    
    def _extract_content_features(self, content: str) -> List[str]:
        """提取内容特征"""
        cleaned = self._clean_content(content)
        
        # 提取关键词（长度大于2的词）
        words = [word for word in cleaned.split() if len(word) > 2]
        
        # 按词频排序，取前20个关键词
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        return [word for word, freq in top_words]
    
    def calculate_similarity(self, content1: str, content2: str) -> float:
        """计算两个内容的相似度"""
        if not content1 or not content2:
            return 0.0
        
        # 清理内容
        clean1 = self._clean_content(content1)
        clean2 = self._clean_content(content2)
        
        # 使用 SequenceMatcher 计算相似度
        similarity = SequenceMatcher(None, clean1, clean2).ratio()
        
        return similarity
    
    def calculate_title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度"""
        if not title1 or not title2:
            return 0.0
        
        # 清理标题
        clean1 = self._clean_content(title1)
        clean2 = self._clean_content(title2)
        
        # 标题相似度计算
        similarity = SequenceMatcher(None, clean1, clean2).ratio()
        
        return similarity
    
    async def is_duplicate_content(
        self, 
        db: AsyncSession, 
        title: str, 
        content: str, 
        url: str,
        user_id: str,
        source_id: Optional[str] = None,
        check_days: int = 7
    ) -> Tuple[bool, Optional[Item], str]:
        """
        检查内容是否重复
        返回: (是否重复, 重复的项目, 重复类型)
        """
        
        # 1. URL 精确匹配
        url_duplicate = await self._check_url_duplicate(db, url, user_id, check_days)
        if url_duplicate:
            return True, url_duplicate, "url_exact"
        
        # 2. 内容哈希精确匹配
        content_hash = self.generate_content_hash(content)
        hash_duplicate = await self._check_hash_duplicate(db, content_hash, user_id, check_days)
        if hash_duplicate:
            return True, hash_duplicate, "content_hash"
        
        # 3. 标题相似度检查
        title_duplicate = await self._check_title_similarity(db, title, user_id, check_days)
        if title_duplicate:
            return True, title_duplicate, "title_similar"
        
        # 4. 内容相似度检查（较慢，最后执行）
        content_duplicate = await self._check_content_similarity(db, content, user_id, check_days)
        if content_duplicate:
            return True, content_duplicate, "content_similar"
        
        return False, None, "unique"
    
    async def _check_url_duplicate(
        self, 
        db: AsyncSession, 
        url: str, 
        user_id: str, 
        check_days: int
    ) -> Optional[Item]:
        """检查 URL 是否重复"""
        if not url:
            return None
        
        cutoff_date = datetime.utcnow() - timedelta(days=check_days)
        
        query = select(Item).where(
            and_(
                Item.url == url,
                Item.source.has(user_id=user_id),
                Item.created_at >= cutoff_date
            )
        ).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _check_hash_duplicate(
        self, 
        db: AsyncSession, 
        content_hash: str, 
        user_id: str, 
        check_days: int
    ) -> Optional[Item]:
        """检查内容哈希是否重复"""
        if not content_hash:
            return None
        
        cutoff_date = datetime.utcnow() - timedelta(days=check_days)
        
        query = select(Item).where(
            and_(
                Item.content_hash == content_hash,
                Item.source.has(user_id=user_id),
                Item.created_at >= cutoff_date
            )
        ).limit(1)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _check_title_similarity(
        self, 
        db: AsyncSession, 
        title: str, 
        user_id: str, 
        check_days: int
    ) -> Optional[Item]:
        """检查标题相似度"""
        if not title or len(title) < 10:  # 标题太短不检查
            return None
        
        cutoff_date = datetime.utcnow() - timedelta(days=check_days)
        
        # 获取最近的标题进行比较
        query = select(Item.id, Item.title).where(
            and_(
                Item.source.has(user_id=user_id),
                Item.created_at >= cutoff_date,
                func.length(Item.title) > 10
            )
        ).limit(100)  # 限制比较数量
        
        result = await db.execute(query)
        recent_items = result.fetchall()
        
        # 逐一比较标题相似度
        for item_id, item_title in recent_items:
            similarity = self.calculate_title_similarity(title, item_title)
            if similarity >= self.title_similarity_threshold:
                # 返回完整的 Item 对象
                item_query = select(Item).where(Item.id == item_id)
                item_result = await db.execute(item_query)
                return item_result.scalar_one_or_none()
        
        return None
    
    async def _check_content_similarity(
        self, 
        db: AsyncSession, 
        content: str, 
        user_id: str, 
        check_days: int
    ) -> Optional[Item]:
        """检查内容相似度（较慢的操作）"""
        if not content or len(content) < 100:  # 内容太短不检查
            return None
        
        # 先检查缓存
        cache_key = f"content_similarity:{user_id}:{hashlib.md5(content.encode()).hexdigest()[:16]}"
        cached_result = await cache_manager.get(cache_key)
        if cached_result is not None:
            if cached_result == "no_duplicate":
                return None
            else:
                # 返回缓存的重复项 ID
                item_query = select(Item).where(Item.id == cached_result)
                result = await db.execute(item_query)
                return result.scalar_one_or_none()
        
        cutoff_date = datetime.utcnow() - timedelta(days=check_days)
        
        # 使用模糊哈希进行初筛
        fuzzy_hash = self.generate_fuzzy_hash(content)
        
        # 获取相似的模糊哈希
        query = select(Item.id, Item.content, Item.fuzzy_hash).where(
            and_(
                Item.source.has(user_id=user_id),
                Item.created_at >= cutoff_date,
                Item.fuzzy_hash.isnot(None),
                func.length(Item.content) > 100
            )
        ).limit(50)  # 限制比较数量
        
        result = await db.execute(query)
        recent_items = result.fetchall()
        
        # 首先通过模糊哈希快速筛选
        candidates = []
        for item_id, item_content, item_fuzzy_hash in recent_items:
            if item_fuzzy_hash and self._fuzzy_hash_similar(fuzzy_hash, item_fuzzy_hash):
                candidates.append((item_id, item_content))
        
        # 对候选项进行详细相似度比较
        for item_id, item_content in candidates:
            similarity = self.calculate_similarity(content, item_content)
            if similarity >= self.similarity_threshold:
                # 缓存结果
                await cache_manager.set(cache_key, item_id, ttl=3600)  # 缓存1小时
                
                # 返回完整的 Item 对象
                item_query = select(Item).where(Item.id == item_id)
                item_result = await db.execute(item_query)
                return item_result.scalar_one_or_none()
        
        # 没有找到重复，缓存结果
        await cache_manager.set(cache_key, "no_duplicate", ttl=3600)
        return None
    
    def _fuzzy_hash_similar(self, hash1: str, hash2: str, threshold: float = 0.6) -> bool:
        """比较两个模糊哈希是否相似"""
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return False
        
        # 计算汉明距离
        hamming_distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        similarity = 1 - (hamming_distance / len(hash1))
        
        return similarity >= threshold
    
    async def batch_deduplicate(
        self, 
        db: AsyncSession, 
        items: List[Dict[str, Any]], 
        user_id: str
    ) -> List[Dict[str, Any]]:
        """批量去重处理"""
        unique_items = []
        seen_hashes = set()
        seen_urls = set()
        
        for item_data in items:
            title = item_data.get('title', '')
            content = item_data.get('content', '')
            url = item_data.get('url', '')
            
            # 快速去重检查
            if url and url in seen_urls:
                continue
            
            content_hash = self.generate_content_hash(content)
            if content_hash and content_hash in seen_hashes:
                continue
            
            # 详细去重检查
            is_duplicate, duplicate_item, duplicate_type = await self.is_duplicate_content(
                db, title, content, url, user_id
            )
            
            if not is_duplicate:
                # 添加到唯一项目列表
                item_data['content_hash'] = content_hash
                item_data['fuzzy_hash'] = self.generate_fuzzy_hash(content)
                unique_items.append(item_data)
                
                # 记录已见过的哈希和URL
                if content_hash:
                    seen_hashes.add(content_hash)
                if url:
                    seen_urls.add(url)
            else:
                logger.info(
                    "Duplicate content detected",
                    title=title[:50],
                    duplicate_type=duplicate_type,
                    original_item_id=duplicate_item.id if duplicate_item else None
                )
        
        return unique_items
    
    async def get_duplicate_stats(self, db: AsyncSession, user_id: str, days: int = 30) -> Dict[str, Any]:
        """获取去重统计信息"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 总项目数
        total_query = select(func.count(Item.id)).where(
            and_(
                Item.source.has(user_id=user_id),
                Item.created_at >= cutoff_date
            )
        )
        total_result = await db.execute(total_query)
        total_items = total_result.scalar() or 0
        
        # 有重复哈希的项目数
        duplicate_hash_query = select(func.count(Item.id)).where(
            and_(
                Item.source.has(user_id=user_id),
                Item.created_at >= cutoff_date,
                Item.content_hash.in_(
                    select(Item.content_hash)
                    .where(Item.content_hash.isnot(None))
                    .group_by(Item.content_hash)
                    .having(func.count(Item.id) > 1)
                )
            )
        )
        duplicate_hash_result = await db.execute(duplicate_hash_query)
        duplicate_by_hash = duplicate_hash_result.scalar() or 0
        
        # 有重复URL的项目数
        duplicate_url_query = select(func.count(Item.id)).where(
            and_(
                Item.source.has(user_id=user_id),
                Item.created_at >= cutoff_date,
                Item.url.in_(
                    select(Item.url)
                    .where(Item.url.isnot(None))
                    .group_by(Item.url)
                    .having(func.count(Item.id) > 1)
                )
            )
        )
        duplicate_url_result = await db.execute(duplicate_url_query)
        duplicate_by_url = duplicate_url_result.scalar() or 0
        
        return {
            "total_items": total_items,
            "duplicate_by_hash": duplicate_by_hash,
            "duplicate_by_url": duplicate_by_url,
            "unique_items": total_items - max(duplicate_by_hash, duplicate_by_url),
            "deduplication_rate": (max(duplicate_by_hash, duplicate_by_url) / total_items * 100) if total_items > 0 else 0,
            "period_days": days
        }


# 全局去重器实例
content_deduplicator = ContentDeduplicator()