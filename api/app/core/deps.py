"""
Dependencies - Linus style: explicit is better than magic.
"If you need it, import it. If it fails, handle it. No magic."
"""

import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class Feature:
    """A feature that might or might not be available"""
    def __init__(self, name: str, module: Optional[object] = None):
        self.name = name
        self.available = module is not None
        self.module = module


@lru_cache(maxsize=None)
def check_openai() -> Feature:
    """Check if OpenAI is available - simple and cached"""
    try:
        import openai
        return Feature("openai", openai)
    except ImportError:
        logger.info("OpenAI not available - install 'openai' to enable")
        return Feature("openai", None)


@lru_cache(maxsize=None)
def check_anthropic() -> Feature:
    """Check if Anthropic is available"""
    try:
        import anthropic
        return Feature("anthropic", anthropic)
    except ImportError:
        logger.info("Anthropic not available - install 'anthropic' to enable")
        return Feature("anthropic", None)


@lru_cache(maxsize=None)
def check_redis() -> Feature:
    """Check if Redis is available"""
    try:
        import redis
        # Actually try to connect
        client = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1)
        client.ping()
        return Feature("redis", redis)
    except (ImportError, Exception) as e:
        logger.info(f"Redis not available: {e}")
        return Feature("redis", None)


def get_available_features() -> dict:
    """Get all available features - no magic, just checks"""
    return {
        "openai": check_openai().available,
        "anthropic": check_anthropic().available,
        "redis": check_redis().available,
    }


# Direct access to features - no managers, no factories
openai_feature = check_openai()
anthropic_feature = check_anthropic()
redis_feature = check_redis()