"""
Feature manager for AttentionSync - placeholder implementation
Following Linus's principle: "Do one thing well"
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Feature:
    """Base feature class"""
    
    def __init__(self, name: str):
        self.name = name
        self._loaded = False
        self._failed = False
        self._instance = None
    
    def load(self):
        """Load the feature"""
        if not self._loaded and not self._failed:
            try:
                self._instance = self._load_implementation()
                self._loaded = True
                logger.info(f"Feature loaded: {self.name}")
            except Exception as e:
                self._failed = True
                logger.warning(f"Feature failed to load: {self.name}, error: {e}")
    
    def _load_implementation(self):
        """Override in subclasses"""
        return None
    
    def get_instance(self):
        """Get the loaded instance"""
        if not self._loaded:
            self.load()
        return self._instance if self._loaded else None


class FeatureManager:
    """Manages feature loading and availability"""
    
    def __init__(self):
        self.features = {}
        self._initialized = False
    
    def register_feature(self, name: str, feature: Feature):
        """Register a feature"""
        self.features[name] = feature
    
    def get_feature(self, name: str) -> Optional[Feature]:
        """Get a feature by name"""
        return self.features.get(name)
    
    def get_feature_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all features"""
        status = {}
        for name, feature in self.features.items():
            status[name] = {
                "loaded": feature._loaded,
                "failed": feature._failed,
                "available": feature._loaded and not feature._failed
            }
        return status


# Global feature manager instance
_feature_manager = FeatureManager()


def get_feature_manager() -> FeatureManager:
    """Get the global feature manager"""
    return _feature_manager


def requires_feature(feature_name: str):
    """Decorator for functions that require a specific feature"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_feature_manager()
            feature = manager.get_feature(feature_name)
            if not feature or not feature._loaded:
                raise RuntimeError(f"Required feature '{feature_name}' not available")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def optional_feature(feature_name: str):
    """Decorator for functions that can use an optional feature"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_feature_manager()
            feature = manager.get_feature(feature_name)
            if feature and feature._loaded:
                return func(feature.get_instance(), *args, **kwargs)
            else:
                return func(None, *args, **kwargs)
        return wrapper
    return decorator


def get_smart_feature_flags() -> Dict[str, bool]:
    """Get feature availability flags"""
    manager = get_feature_manager()
    flags = {}
    for name, feature in manager.features.items():
        flags[name] = feature._loaded and not feature._failed
    return flags
