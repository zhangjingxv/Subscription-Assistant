"""
Feature manager with intelligent loading - Linus style: lazy loading, smart caching
"Load what you need, when you need it, and cache it forever."
"""

import asyncio
from typing import Dict, Any, Optional, Callable, TypeVar, Generic
from functools import wraps, lru_cache
from dataclasses import dataclass
import structlog

from app.core.smart_deps import get_dependency_manager, FeatureLevel

logger = structlog.get_logger()

T = TypeVar('T')


@dataclass
class FeatureContext:
    """Context for feature execution"""
    feature_name: str
    required_deps: List[str]
    fallback_available: bool
    performance_cost: str  # "low", "medium", "high"


class LazyFeature(Generic[T]):
    """Lazy-loaded feature - like kernel module loading"""
    
    def __init__(self, 
                 feature_name: str,
                 loader: Callable[[], T],
                 required_deps: List[str],
                 fallback: Optional[Callable[[], T]] = None):
        self.feature_name = feature_name
        self.loader = loader
        self.required_deps = required_deps
        self.fallback = fallback
        self._instance: Optional[T] = None
        self._loaded = False
        self._failed = False
    
    def is_available(self) -> bool:
        """Check if feature can be loaded"""
        if self._loaded:
            return not self._failed
        
        manager = get_dependency_manager()
        return all(
            manager.available_features.get(dep, False) 
            for dep in self.required_deps
        )
    
    def get(self) -> Optional[T]:
        """Get feature instance - lazy loading with caching"""
        if self._loaded:
            return self._instance if not self._failed else None
        
        try:
            if self.is_available():
                logger.debug(f"🔄 Loading feature: {self.feature_name}")
                self._instance = self.loader()
                logger.info(f"✅ Feature loaded: {self.feature_name}")
            else:
                logger.debug(f"⚠️  Feature unavailable: {self.feature_name}")
                if self.fallback:
                    logger.debug(f"🔄 Loading fallback for: {self.feature_name}")
                    self._instance = self.fallback()
                    logger.info(f"✅ Fallback loaded: {self.feature_name}")
                else:
                    self._failed = True
        
        except Exception as e:
            logger.error(f"💥 Feature loading failed: {self.feature_name}", error=str(e))
            self._failed = True
            if self.fallback:
                try:
                    self._instance = self.fallback()
                    logger.info(f"✅ Fallback rescued: {self.feature_name}")
                except Exception as fallback_error:
                    logger.error(f"💥 Fallback also failed: {self.feature_name}", error=str(fallback_error))
        
        finally:
            self._loaded = True
        
        return self._instance if not self._failed else None


class FeatureManager:
    """Central feature manager - like kernel subsystem manager"""
    
    def __init__(self):
        self.features: Dict[str, LazyFeature] = {}
        self.performance_cache: Dict[str, float] = {}
        self._setup_features()
    
    def _setup_features(self):
        """Setup all lazy features"""
        
        # AI Summarization
        self.features["ai_summarizer"] = LazyFeature(
            feature_name="ai_summarizer",
            loader=self._load_ai_summarizer,
            required_deps=["anthropic"],
            fallback=self._load_simple_summarizer
        )
        
        # ML Embeddings
        self.features["ml_embedder"] = LazyFeature(
            feature_name="ml_embedder",
            loader=self._load_ml_embedder,
            required_deps=["sentence_transformers"],
            fallback=self._load_simple_embedder
        )
        
        # Image Processor
        self.features["image_processor"] = LazyFeature(
            feature_name="image_processor", 
            loader=self._load_image_processor,
            required_deps=["PIL"],
            fallback=self._load_basic_image_info
        )
        
        # Document Processor
        self.features["document_processor"] = LazyFeature(
            feature_name="document_processor",
            loader=self._load_document_processor,
            required_deps=["pypdf"],
            fallback=self._load_basic_text_extractor
        )
    
    def get_feature(self, feature_name: str) -> Optional[Any]:
        """Get feature instance - intelligent loading"""
        feature = self.features.get(feature_name)
        if not feature:
            logger.warning(f"Unknown feature requested: {feature_name}")
            return None
        
        return feature.get()
    
    def get_available_features(self) -> Dict[str, bool]:
        """Get list of available features"""
        return {
            name: feature.is_available() 
            for name, feature in self.features.items()
        }
    
    def get_feature_status(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed feature status"""
        status = {}
        for name, feature in self.features.items():
            status[name] = {
                "available": feature.is_available(),
                "loaded": feature._loaded,
                "failed": feature._failed,
                "has_fallback": feature.fallback is not None,
                "required_deps": feature.required_deps
            }
        return status
    
    # Feature loaders
    def _load_ai_summarizer(self):
        """Load AI summarizer"""
        import anthropic
        return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    def _load_simple_summarizer(self):
        """Simple text summarizer fallback"""
        class SimpleSummarizer:
            def summarize(self, text: str, max_length: int = 200) -> str:
                if len(text) <= max_length:
                    return text
                
                # Smart truncation at sentence boundaries
                truncated = text[:max_length]
                boundaries = ['。', '！', '？', '.', '!', '?']
                
                for boundary in boundaries:
                    last_pos = truncated.rfind(boundary)
                    if last_pos > max_length * 0.7:  # At least 70% of target length
                        return text[:last_pos + 1]
                
                return text[:max_length - 3] + "..."
        
        return SimpleSummarizer()
    
    def _load_ml_embedder(self):
        """Load ML embedder"""
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('all-MiniLM-L6-v2')
    
    def _load_simple_embedder(self):
        """Simple hash-based embedder fallback"""
        import hashlib
        
        class SimpleEmbedder:
            def encode(self, texts: List[str]) -> List[List[float]]:
                """Simple hash-based embeddings"""
                embeddings = []
                for text in texts:
                    # Create deterministic hash-based embedding
                    hash_val = hashlib.md5(text.encode()).hexdigest()
                    # Convert hex to float vector (simplified)
                    embedding = [float(int(hash_val[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]
                    embeddings.append(embedding)
                return embeddings
        
        return SimpleEmbedder()
    
    def _load_image_processor(self):
        """Load PIL image processor"""
        from PIL import Image
        return Image
    
    def _load_basic_image_info(self):
        """Basic image info extractor"""
        class BasicImageInfo:
            def open(self, file_path):
                # Return basic file info without actual image processing
                return {"type": "image", "processor": "basic"}
        
        return BasicImageInfo()
    
    def _load_document_processor(self):
        """Load PDF processor"""
        import pypdf
        return pypdf.PdfReader
    
    def _load_basic_text_extractor(self):
        """Basic text extractor fallback"""
        class BasicTextExtractor:
            def __init__(self, file_data):
                self.file_data = file_data
            
            def extract_text(self) -> str:
                # Try to extract basic text (very limited)
                try:
                    return self.file_data.decode('utf-8', errors='ignore')[:1000]
                except:
                    return "Text extraction not available (install pypdf for PDF support)"
        
        return BasicTextExtractor


# Decorators for feature-dependent functions
def requires_feature(feature_name: str, graceful: bool = True):
    """Decorator to require specific features"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_feature_manager()
            feature = manager.get_feature(feature_name)
            
            if feature is None:
                if graceful:
                    logger.warning(f"Feature {feature_name} not available, skipping {func.__name__}")
                    return None
                else:
                    raise RuntimeError(f"Required feature {feature_name} not available")
            
            # Inject feature as first argument
            return await func(feature, *args, **kwargs)
        
        return wrapper
    return decorator


def optional_feature(feature_name: str, default_return=None):
    """Decorator for optional features with default return"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            manager = get_feature_manager()
            feature = manager.get_feature(feature_name)
            
            if feature is None:
                logger.debug(f"Optional feature {feature_name} not available")
                return default_return
            
            try:
                return await func(feature, *args, **kwargs)
            except Exception as e:
                logger.warning(f"Feature {feature_name} failed", error=str(e))
                return default_return
        
        return wrapper
    return decorator


# Global feature manager
_feature_manager = FeatureManager()


def get_feature_manager() -> FeatureManager:
    """Get global feature manager"""
    return _feature_manager


@lru_cache()
def get_smart_feature_flags() -> Dict[str, bool]:
    """Get cached smart feature flags"""
    manager = get_dependency_manager()
    if not manager.available_features:
        manager.scan_environment()
    
    return manager.create_feature_flags()