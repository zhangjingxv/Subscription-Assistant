"""
Smart dependency manager - Linus style: intelligent, automatic, transparent
"The best interface is no interface. The best configuration is no configuration."
"""

import os
import sys
import subprocess
import importlib
from typing import Dict, List, Optional, Set, Callable
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()


class FeatureLevel(Enum):
    """Feature importance levels - like kernel module priorities"""
    CRITICAL = "critical"    # Core functionality, must work
    ENHANCED = "enhanced"    # Nice to have, graceful degradation
    OPTIONAL = "optional"    # Luxury features, can be missing


@dataclass
class SmartDependency:
    """Smart dependency definition"""
    name: str
    import_name: str
    pip_package: str
    feature_level: FeatureLevel
    description: str
    auto_install: bool = False
    fallback_available: bool = True
    test_import: Optional[str] = None


class DependencyManager:
    """Intelligent dependency manager - like kernel module loader"""
    
    def __init__(self):
        self.dependencies = self._define_dependencies()
        self.available_features: Dict[str, bool] = {}
        self.missing_critical: List[str] = []
        self.installation_queue: List[SmartDependency] = []
        
    def _define_dependencies(self) -> Dict[str, SmartDependency]:
        """Define all possible dependencies with smart metadata"""
        return {
            # AI Services
            "anthropic": SmartDependency(
                name="anthropic",
                import_name="anthropic",
                pip_package="anthropic>=0.7.8",
                feature_level=FeatureLevel.ENHANCED,
                description="Claude AI for advanced summarization",
                auto_install=True,
                test_import="anthropic.Anthropic"
            ),
            
            "openai": SmartDependency(
                name="openai", 
                import_name="openai",
                pip_package="openai>=1.3.8",
                feature_level=FeatureLevel.ENHANCED,
                description="OpenAI GPT for text processing",
                auto_install=True,
                test_import="openai.OpenAI"
            ),
            
            # ML Processing
            "sentence_transformers": SmartDependency(
                name="sentence_transformers",
                import_name="sentence_transformers", 
                pip_package="sentence-transformers>=3.1.0",
                feature_level=FeatureLevel.ENHANCED,
                description="Semantic embeddings and clustering",
                auto_install=False,  # Large download
                test_import="sentence_transformers.SentenceTransformer"
            ),
            
            "sklearn": SmartDependency(
                name="sklearn",
                import_name="sklearn",
                pip_package="scikit-learn>=1.5.0",
                feature_level=FeatureLevel.ENHANCED,
                description="Machine learning algorithms",
                auto_install=False,
                test_import="sklearn.cluster.KMeans"
            ),
            
            # Media Processing
            "PIL": SmartDependency(
                name="PIL",
                import_name="PIL",
                pip_package="pillow>=10.3.0",
                feature_level=FeatureLevel.OPTIONAL,
                description="Image processing and manipulation",
                auto_install=True,
                test_import="PIL.Image"
            ),
            
            "cv2": SmartDependency(
                name="cv2",
                import_name="cv2", 
                pip_package="opencv-python>=4.8.1.78",
                feature_level=FeatureLevel.OPTIONAL,
                description="Computer vision and image analysis",
                auto_install=False,  # Large package
                test_import="cv2.imread"
            ),
            
            # Document Processing
            "pypdf": SmartDependency(
                name="pypdf",
                import_name="pypdf",
                pip_package="pypdf>=4.0.1",
                feature_level=FeatureLevel.ENHANCED,
                description="PDF document processing",
                auto_install=True,
                test_import="pypdf.PdfReader"
            ),
            
            # Data Analysis
            "pandas": SmartDependency(
                name="pandas",
                import_name="pandas",
                pip_package="pandas>=2.1.4",
                feature_level=FeatureLevel.OPTIONAL,
                description="Data analysis and manipulation",
                auto_install=False,  # Heavy dependency
                test_import="pandas.DataFrame"
            ),
            
            # Development Tools
            "ruff": SmartDependency(
                name="ruff",
                import_name="ruff",
                pip_package="ruff>=0.1.9",
                feature_level=FeatureLevel.OPTIONAL,
                description="Fast Python linter and formatter",
                auto_install=True,
                test_import="ruff.api"
            ),
        }
    
    def scan_environment(self) -> Dict[str, bool]:
        """Scan current environment for available dependencies"""
        logger.info("🔍 Scanning dependency environment...")
        
        results = {}
        for name, dep in self.dependencies.items():
            available = self._test_dependency(dep)
            results[name] = available
            
            if available:
                logger.debug(f"✅ {dep.description}")
            else:
                logger.debug(f"❌ {dep.description}")
                
                if dep.feature_level == FeatureLevel.CRITICAL:
                    self.missing_critical.append(name)
                elif dep.auto_install and self._should_auto_install(dep):
                    self.installation_queue.append(dep)
        
        self.available_features = results
        return results
    
    def _test_dependency(self, dep: SmartDependency) -> bool:
        """Test if dependency is available and working"""
        try:
            # Basic import test
            module = importlib.import_module(dep.import_name)
            
            # Advanced test if specified
            if dep.test_import:
                parts = dep.test_import.split('.')
                obj = module
                for part in parts[1:]:  # Skip module name
                    obj = getattr(obj, part)
            
            return True
        except (ImportError, AttributeError):
            return False
    
    def _should_auto_install(self, dep: SmartDependency) -> bool:
        """Decide if dependency should be auto-installed"""
        # Check if user wants auto-install
        auto_install_env = os.getenv("ATTENTIONSYNC_AUTO_INSTALL", "true").lower()
        if auto_install_env not in ("true", "1", "yes"):
            return False
        
        # Check if in development mode
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            return False  # Never auto-install in production
        
        # Check if package is small enough for auto-install
        large_packages = {"sentence-transformers", "opencv-python", "pandas"}
        if dep.pip_package.split(">=")[0] in large_packages:
            return False
        
        return True
    
    async def auto_install_missing(self) -> bool:
        """Auto-install missing dependencies - like kernel module auto-loading"""
        if not self.installation_queue:
            return True
        
        logger.info(f"🔄 Auto-installing {len(self.installation_queue)} dependencies...")
        
        success_count = 0
        for dep in self.installation_queue:
            try:
                logger.info(f"📦 Installing {dep.name}...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "--break-system-packages", "--user", dep.pip_package
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info(f"✅ {dep.name} installed successfully")
                    success_count += 1
                else:
                    logger.warning(f"❌ {dep.name} installation failed", error=result.stderr)
            
            except subprocess.TimeoutExpired:
                logger.error(f"⏰ {dep.name} installation timed out")
            except Exception as e:
                logger.error(f"💥 {dep.name} installation error", error=str(e))
        
        logger.info(f"📊 Auto-installation complete: {success_count}/{len(self.installation_queue)}")
        
        # Re-scan after installation
        if success_count > 0:
            self.scan_environment()
        
        return success_count == len(self.installation_queue)
    
    def get_feature_recommendations(self) -> Dict[str, str]:
        """Get recommendations for missing features"""
        recommendations = {}
        
        for name, dep in self.dependencies.items():
            if not self.available_features.get(name, False):
                if dep.feature_level == FeatureLevel.ENHANCED:
                    recommendations[dep.description] = f"pip install {dep.pip_package}"
                elif dep.feature_level == FeatureLevel.OPTIONAL:
                    recommendations[dep.description] = f"pip install {dep.pip_package} (optional)"
        
        return recommendations
    
    def create_feature_flags(self) -> Dict[str, bool]:
        """Create feature flags based on available dependencies"""
        return {
            "ai_summarization": self.available_features.get("anthropic", False) or 
                              self.available_features.get("openai", False),
            "ml_clustering": self.available_features.get("sentence_transformers", False),
            "ml_analysis": self.available_features.get("sklearn", False),
            "image_processing": self.available_features.get("PIL", False),
            "computer_vision": self.available_features.get("cv2", False),
            "document_processing": self.available_features.get("pypdf", False),
            "data_analysis": self.available_features.get("pandas", False),
            "code_quality": self.available_features.get("ruff", False),
        }
    
    def generate_install_commands(self) -> Dict[str, str]:
        """Generate install commands for missing feature groups"""
        commands = {}
        
        # Group dependencies by feature area
        feature_groups = {
            "AI Services": ["anthropic", "openai"],
            "ML Processing": ["sentence_transformers", "sklearn"],
            "Media Processing": ["PIL", "cv2"],
            "Document Processing": ["pypdf"],
            "Data Analysis": ["pandas"],
            "Development Tools": ["ruff"]
        }
        
        for group_name, deps in feature_groups.items():
            missing_deps = [
                self.dependencies[dep_name].pip_package 
                for dep_name in deps 
                if not self.available_features.get(dep_name, False)
                and dep_name in self.dependencies
            ]
            
            if missing_deps:
                commands[group_name] = f"pip install {' '.join(missing_deps)}"
        
        return commands


# Global dependency manager
_dependency_manager = DependencyManager()


def get_dependency_manager() -> DependencyManager:
    """Get global dependency manager"""
    return _dependency_manager


async def initialize_smart_dependencies() -> Dict[str, bool]:
    """Initialize smart dependency system - entry point"""
    manager = get_dependency_manager()
    
    # Scan current environment
    available = manager.scan_environment()
    
    # Auto-install if enabled and appropriate
    if manager.installation_queue:
        auto_install_enabled = os.getenv("ATTENTIONSYNC_AUTO_INSTALL", "true").lower() in ("true", "1", "yes")
        environment = os.getenv("ENVIRONMENT", "development")
        
        if auto_install_enabled and environment == "development":
            logger.info("🤖 Auto-installation enabled, installing missing dependencies...")
            await manager.auto_install_missing()
        else:
            logger.info("ℹ️  Auto-installation disabled or in production mode")
            recommendations = manager.get_feature_recommendations()
            if recommendations:
                logger.info("💡 Feature recommendations available", recommendations=recommendations)
    
    # Log final status
    feature_flags = manager.create_feature_flags()
    enabled_count = sum(feature_flags.values())
    total_count = len(feature_flags)
    
    logger.info(
        "🎯 Dependency initialization complete",
        enabled_features=enabled_count,
        total_features=total_count,
        features=feature_flags
    )
    
    return feature_flags