"""
AI智能优化系统
包含多模型支持、智能推荐、内容分析、用户行为学习等
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict
import hashlib

import os
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

try:
    import tiktoken
except ImportError:
    tiktoken = None

from app.core.global_config import get_global_config, Region
from app.core.performance_optimizer import cached, get_cache
from app.core.logging_config import get_logger
from app.models.global_user import GlobalUser

logger = get_logger(__name__)


class AIModel(str, Enum):
    """AI模型类型"""
    OPENAI_GPT4 = "gpt-4"
    OPENAI_GPT35 = "gpt-3.5-turbo"
    ANTHROPIC_CLAUDE = "claude-3-sonnet-20240229"
    ANTHROPIC_HAIKU = "claude-3-haiku-20240307"
    LOCAL_LLAMA = "llama-2-7b-chat"


class ContentType(str, Enum):
    """内容类型"""
    NEWS = "news"
    BLOG = "blog"
    SOCIAL = "social"
    VIDEO = "video"
    PODCAST = "podcast"
    ACADEMIC = "academic"


@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    summary: str
    sentiment_score: float  # -1 to 1
    importance_score: float  # 0 to 1
    topics: List[str]
    entities: List[str]
    reading_time: int  # minutes
    difficulty_level: str  # beginner, intermediate, advanced
    language: str
    confidence: float  # 0 to 1


@dataclass
class PersonalizationProfile:
    """个性化用户画像"""
    user_id: str
    interests: Dict[str, float]  # topic -> interest_score
    reading_patterns: Dict[str, Any]
    engagement_history: List[Dict[str, Any]]
    preferred_content_types: List[ContentType]
    reading_speed: float  # words per minute
    active_hours: List[int]  # hours of day when most active
    language_preferences: List[str]
    last_updated: datetime


class MultiModelAIService:
    """多模型AI服务"""
    
    def __init__(self):
        self.config_manager = get_global_config()
        self.openai_client = None
        self.anthropic_client = None
        self.local_models = {}
        self.token_encoders = {}
        
        self._init_clients()
    
    def _init_clients(self):
        """初始化AI客户端"""
        try:
            # OpenAI
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = openai.AsyncOpenAI(api_key=openai_key)
                self.token_encoders["gpt"] = tiktoken.encoding_for_model("gpt-4")
            
            # Anthropic
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key:
                self.anthropic_client = anthropic.AsyncAnthropic(api_key=anthropic_key)
            
            logger.info("AI clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI clients: {e}")
    
    async def analyze_content(self, content: str, content_type: ContentType = ContentType.NEWS,
                            model: AIModel = AIModel.ANTHROPIC_CLAUDE,
                            language: str = "en") -> AIAnalysisResult:
        """分析内容"""
        
        # 构建分析提示
        analysis_prompt = self._build_analysis_prompt(content, content_type, language)
        
        try:
            if model.value.startswith("gpt"):
                result = await self._analyze_with_openai(analysis_prompt, model)
            elif model.value.startswith("claude"):
                result = await self._analyze_with_anthropic(analysis_prompt, model)
            else:
                result = await self._analyze_with_local_model(analysis_prompt, model)
            
            return self._parse_analysis_result(result, content, language)
            
        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return self._fallback_analysis(content, language)
    
    def _build_analysis_prompt(self, content: str, content_type: ContentType, language: str) -> str:
        """构建分析提示"""
        prompt = f"""
        Please analyze the following {content_type.value} content and provide a structured analysis:

        Content: {content[:2000]}...

        Please provide:
        1. A concise summary (2-3 sentences)
        2. Sentiment score (-1 to 1, where -1 is very negative, 0 is neutral, 1 is very positive)
        3. Importance score (0 to 1, where 1 is extremely important/newsworthy)
        4. Main topics (3-5 key topics)
        5. Named entities (people, organizations, locations)
        6. Estimated reading time in minutes
        7. Difficulty level (beginner/intermediate/advanced)
        8. Primary language
        9. Confidence in analysis (0 to 1)

        Respond in JSON format with these keys: summary, sentiment_score, importance_score, 
        topics, entities, reading_time, difficulty_level, language, confidence
        """
        
        return prompt
    
    async def _analyze_with_openai(self, prompt: str, model: AIModel) -> str:
        """使用OpenAI分析"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        response = await self.openai_client.chat.completions.create(
            model=model.value,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    async def _analyze_with_anthropic(self, prompt: str, model: AIModel) -> str:
        """使用Anthropic分析"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        response = await self.anthropic_client.messages.create(
            model=model.value,
            max_tokens=1000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _analyze_with_local_model(self, prompt: str, model: AIModel) -> str:
        """使用本地模型分析"""
        # 这里可以集成本地LLM模型
        # 暂时返回简化分析
        return json.dumps({
            "summary": "Content analysis using local model",
            "sentiment_score": 0.0,
            "importance_score": 0.5,
            "topics": ["general"],
            "entities": [],
            "reading_time": 5,
            "difficulty_level": "intermediate",
            "language": "en",
            "confidence": 0.7
        })
    
    def _parse_analysis_result(self, result: str, content: str, language: str) -> AIAnalysisResult:
        """解析分析结果"""
        try:
            data = json.loads(result)
            return AIAnalysisResult(
                summary=data.get("summary", ""),
                sentiment_score=float(data.get("sentiment_score", 0.0)),
                importance_score=float(data.get("importance_score", 0.5)),
                topics=data.get("topics", []),
                entities=data.get("entities", []),
                reading_time=int(data.get("reading_time", 5)),
                difficulty_level=data.get("difficulty_level", "intermediate"),
                language=data.get("language", language),
                confidence=float(data.get("confidence", 0.7))
            )
        except Exception as e:
            logger.error(f"Failed to parse AI analysis result: {e}")
            return self._fallback_analysis(content, language)
    
    def _fallback_analysis(self, content: str, language: str) -> AIAnalysisResult:
        """备用分析方法"""
        word_count = len(content.split())
        reading_time = max(1, word_count // 200)  # 假设每分钟200词
        
        return AIAnalysisResult(
            summary="Content analysis unavailable",
            sentiment_score=0.0,
            importance_score=0.5,
            topics=["general"],
            entities=[],
            reading_time=reading_time,
            difficulty_level="intermediate",
            language=language,
            confidence=0.3
        )


class PersonalizationEngine:
    """个性化推荐引擎"""
    
    def __init__(self):
        self.ai_service = MultiModelAIService()
        self.user_profiles: Dict[str, PersonalizationProfile] = {}
        self.content_embeddings: Dict[str, np.ndarray] = {}
    
    async def get_user_profile(self, user: GlobalUser) -> PersonalizationProfile:
        """获取用户画像"""
        profile_key = f"user_profile:{user.id}"
        
        # 尝试从缓存获取
        cache = get_cache()
        cached_profile = await cache.get(profile_key)
        if cached_profile:
            return PersonalizationProfile(**cached_profile)
        
        # 构建用户画像
        profile = await self._build_user_profile(user)
        
        # 缓存用户画像
        await cache.set(profile_key, asdict(profile), config={"ttl": 3600})
        
        return profile
    
    async def _build_user_profile(self, user: GlobalUser) -> PersonalizationProfile:
        """构建用户画像"""
        # 分析用户偏好设置
        interests = self._extract_interests_from_preferences(user.preferences)
        
        # 分析阅读模式
        reading_patterns = self._analyze_reading_patterns(user)
        
        # 获取参与历史
        engagement_history = await self._get_engagement_history(user.id)
        
        # 推断内容类型偏好
        preferred_content_types = self._infer_content_preferences(engagement_history)
        
        # 估算阅读速度
        reading_speed = self._estimate_reading_speed(engagement_history)
        
        # 分析活跃时间
        active_hours = self._analyze_active_hours(engagement_history)
        
        return PersonalizationProfile(
            user_id=str(user.id),
            interests=interests,
            reading_patterns=reading_patterns,
            engagement_history=engagement_history[-50:],  # 保留最近50条
            preferred_content_types=preferred_content_types,
            reading_speed=reading_speed,
            active_hours=active_hours,
            language_preferences=[user.preferred_language],
            last_updated=datetime.utcnow()
        )
    
    def _extract_interests_from_preferences(self, preferences: Dict[str, Any]) -> Dict[str, float]:
        """从用户偏好中提取兴趣"""
        interests = defaultdict(float)
        
        # 从标签偏好中提取
        tags = preferences.get("favorite_tags", [])
        for tag in tags:
            interests[tag] = 0.8
        
        # 从类别偏好中提取
        categories = preferences.get("favorite_categories", [])
        for category in categories:
            interests[category] = 0.7
        
        # 从源偏好中提取
        sources = preferences.get("favorite_sources", [])
        for source in sources:
            interests[f"source_{source}"] = 0.6
        
        return dict(interests)
    
    def _analyze_reading_patterns(self, user: GlobalUser) -> Dict[str, Any]:
        """分析阅读模式"""
        return {
            "preferred_time_zone": user.timezone,
            "language": user.preferred_language,
            "region": user.region,
            "notification_preferences": user.notification_settings,
        }
    
    async def _get_engagement_history(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户参与历史"""
        # 这里应该从数据库查询用户的阅读、点赞、收藏等行为
        # 暂时返回模拟数据
        return []
    
    def _infer_content_preferences(self, engagement_history: List[Dict[str, Any]]) -> List[ContentType]:
        """推断内容类型偏好"""
        content_scores = defaultdict(float)
        
        for engagement in engagement_history:
            content_type = engagement.get("content_type", "news")
            engagement_score = engagement.get("engagement_score", 0.5)
            content_scores[content_type] += engagement_score
        
        # 按分数排序
        sorted_types = sorted(content_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 返回前3个偏好类型
        return [ContentType(ct) for ct, _ in sorted_types[:3]] or [ContentType.NEWS]
    
    def _estimate_reading_speed(self, engagement_history: List[Dict[str, Any]]) -> float:
        """估算阅读速度"""
        reading_times = []
        
        for engagement in engagement_history:
            if engagement.get("action") == "read_complete":
                word_count = engagement.get("word_count", 0)
                time_spent = engagement.get("time_spent", 0)  # seconds
                
                if word_count > 0 and time_spent > 10:  # 至少10秒
                    wpm = (word_count / time_spent) * 60
                    if 50 <= wpm <= 1000:  # 合理范围
                        reading_times.append(wpm)
        
        if reading_times:
            return sum(reading_times) / len(reading_times)
        else:
            return 250.0  # 默认阅读速度
    
    def _analyze_active_hours(self, engagement_history: List[Dict[str, Any]]) -> List[int]:
        """分析活跃时间段"""
        hour_activity = defaultdict(int)
        
        for engagement in engagement_history:
            timestamp = engagement.get("timestamp")
            if timestamp:
                hour = datetime.fromisoformat(timestamp).hour
                hour_activity[hour] += 1
        
        # 返回活跃度前6的时间段
        sorted_hours = sorted(hour_activity.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:6]] or [7, 8, 12, 18, 19, 21]  # 默认活跃时间
    
    @cached(ttl=1800, prefix="recommendations")
    async def get_personalized_recommendations(self, user: GlobalUser, 
                                             available_content: List[Dict[str, Any]],
                                             limit: int = 10) -> List[Dict[str, Any]]:
        """获取个性化推荐"""
        profile = await self.get_user_profile(user)
        
        # 计算内容分数
        scored_content = []
        for content in available_content:
            score = await self._calculate_content_score(content, profile)
            scored_content.append({
                **content,
                "personalization_score": score
            })
        
        # 按分数排序
        scored_content.sort(key=lambda x: x["personalization_score"], reverse=True)
        
        # 应用多样性过滤
        diverse_content = self._apply_diversity_filter(scored_content, limit)
        
        return diverse_content
    
    async def _calculate_content_score(self, content: Dict[str, Any], 
                                     profile: PersonalizationProfile) -> float:
        """计算内容分数"""
        score = 0.0
        
        # 1. 兴趣匹配 (40%)
        content_topics = content.get("topics", [])
        interest_score = 0.0
        for topic in content_topics:
            if topic in profile.interests:
                interest_score += profile.interests[topic]
        
        if content_topics:
            interest_score /= len(content_topics)
        
        score += interest_score * 0.4
        
        # 2. 时间衰减 (20%)
        published_at = content.get("published_at")
        if published_at:
            time_diff = datetime.utcnow() - datetime.fromisoformat(published_at)
            time_decay = max(0, 1 - (time_diff.total_seconds() / (24 * 3600)))  # 24小时衰减
            score += time_decay * 0.2
        
        # 3. 内容类型偏好 (15%)
        content_type = ContentType(content.get("type", "news"))
        if content_type in profile.preferred_content_types:
            type_preference = (3 - profile.preferred_content_types.index(content_type)) / 3
            score += type_preference * 0.15
        
        # 4. 重要性分数 (15%)
        importance = content.get("importance_score", 0.5)
        score += importance * 0.15
        
        # 5. 语言匹配 (10%)
        content_language = content.get("language", "en")
        if content_language in profile.language_preferences:
            score += 0.1
        
        return min(1.0, score)
    
    def _apply_diversity_filter(self, scored_content: List[Dict[str, Any]], 
                              limit: int) -> List[Dict[str, Any]]:
        """应用多样性过滤"""
        selected = []
        used_sources = set()
        used_topics = set()
        
        for content in scored_content:
            if len(selected) >= limit:
                break
            
            source = content.get("source", "unknown")
            topics = set(content.get("topics", []))
            
            # 多样性检查
            source_diversity = source not in used_sources
            topic_diversity = len(topics & used_topics) < 2  # 最多重复2个话题
            
            if source_diversity or topic_diversity or len(selected) < limit // 2:
                selected.append(content)
                used_sources.add(source)
                used_topics.update(topics)
        
        return selected


class FeedbackLoop:
    """用户反馈循环系统"""
    
    def __init__(self):
        self.personalization_engine = PersonalizationEngine()
    
    async def record_user_action(self, user_id: str, content_id: str, 
                                action: str, metadata: Dict[str, Any] = None):
        """记录用户行为"""
        if metadata is None:
            metadata = {}
        
        feedback_data = {
            "user_id": user_id,
            "content_id": content_id,
            "action": action,  # view, like, share, save, skip, etc.
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata
        }
        
        # 存储到数据库或消息队列
        await self._store_feedback(feedback_data)
        
        # 实时更新用户画像
        await self._update_user_profile(user_id, feedback_data)
    
    async def _store_feedback(self, feedback_data: Dict[str, Any]):
        """存储反馈数据"""
        # 这里应该存储到数据库
        logger.info(f"Feedback recorded: {feedback_data['action']} by {feedback_data['user_id']}")
    
    async def _update_user_profile(self, user_id: str, feedback_data: Dict[str, Any]):
        """更新用户画像"""
        # 实时调整用户兴趣权重
        action = feedback_data["action"]
        content_id = feedback_data["content_id"]
        
        # 根据不同行为调整权重
        weight_adjustments = {
            "like": 0.1,
            "share": 0.15,
            "save": 0.2,
            "skip": -0.05,
            "hide": -0.1,
            "report": -0.2
        }
        
        adjustment = weight_adjustments.get(action, 0)
        
        if adjustment != 0:
            # 更新用户兴趣权重
            # 这里应该根据内容的主题调整用户画像
            pass


# 全局实例
_ai_service_instance = None
_personalization_engine_instance = None
_feedback_loop_instance = None


def get_ai_service() -> MultiModelAIService:
    """获取AI服务实例"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = MultiModelAIService()
    return _ai_service_instance


def get_personalization_engine() -> PersonalizationEngine:
    """获取个性化引擎实例"""
    global _personalization_engine_instance
    if _personalization_engine_instance is None:
        _personalization_engine_instance = PersonalizationEngine()
    return _personalization_engine_instance


def get_feedback_loop() -> FeedbackLoop:
    """获取反馈循环实例"""
    global _feedback_loop_instance
    if _feedback_loop_instance is None:
        _feedback_loop_instance = FeedbackLoop()
    return _feedback_loop_instance