"""
Smart API with intelligent feature loading - Linus style: adaptive functionality
"The system should adapt to what's available, not demand what's missing."
"""

import os
import time
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import structlog

from app.core.feature_manager import (
    get_feature_manager, requires_feature, optional_feature,
    get_smart_feature_flags
)
from app.core.smart_deps import get_dependency_manager

logger = structlog.get_logger()
router = APIRouter()


class ContentRequest(BaseModel):
    """Content processing request"""
    text: str
    options: Dict[str, Any] = {}


class ProcessingResult(BaseModel):
    """Processing result with feature attribution"""
    original_text: str
    processed_data: Dict[str, Any]
    features_used: List[str]
    processing_time_ms: float
    fallback_used: bool = False


@router.get("/features/status")
async def feature_status():
    """Get current feature status - what's working, what's not"""
    manager = get_feature_manager()
    dep_manager = get_dependency_manager()
    
    feature_status = manager.get_feature_status()
    feature_flags = get_smart_feature_flags()
    
    # Get installation recommendations
    recommendations = dep_manager.get_feature_recommendations()
    install_commands = dep_manager.generate_install_commands()
    
    return {
        "feature_flags": feature_flags,
        "feature_status": feature_status,
        "recommendations": recommendations,
        "install_commands": install_commands,
        "auto_install_enabled": os.getenv("ATTENTIONSYNC_AUTO_INSTALL", "true").lower() in ("true", "1", "yes")
    }


@router.post("/features/install/{feature_group}")
async def install_feature_group(feature_group: str, background_tasks: BackgroundTasks):
    """Install feature group on demand - like kernel module loading"""
    dep_manager = get_dependency_manager()
    install_commands = dep_manager.generate_install_commands()
    
    if feature_group not in install_commands:
        raise HTTPException(
            status_code=404, 
            detail=f"Feature group '{feature_group}' not found or already installed"
        )
    
    # Add installation task to background
    background_tasks.add_task(
        _install_feature_group_background,
        feature_group,
        install_commands[feature_group]
    )
    
    return {
        "message": f"Installing {feature_group} in background",
        "command": install_commands[feature_group],
        "status": "queued"
    }


async def _install_feature_group_background(feature_group: str, install_command: str):
    """Background task for feature installation"""
    import subprocess
    import sys
    
    logger.info(f"🔄 Installing feature group: {feature_group}")
    
    try:
        # Parse and execute pip install command
        pip_packages = install_command.replace("pip install ", "").split()
        
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--break-system-packages", "--user"
        ] + pip_packages, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logger.info(f"✅ Feature group installed: {feature_group}")
            
            # Re-scan dependencies
            dep_manager = get_dependency_manager()
            dep_manager.scan_environment()
            
        else:
            logger.error(f"❌ Installation failed: {feature_group}", error=result.stderr)
    
    except Exception as e:
        logger.error(f"💥 Installation error: {feature_group}", error=str(e))


@router.post("/process/smart")
async def smart_process_content(request: ContentRequest) -> ProcessingResult:
    """Smart content processing with adaptive features"""
    start_time = time.time()
    
    result_data = {
        "length": len(request.text),
        "word_count": len(request.text.split())
    }
    features_used = ["basic_analysis"]
    fallback_used = False
    
    # Try AI summarization
    summary = await _try_ai_summarization(request.text)
    if summary:
        result_data["ai_summary"] = summary
        features_used.append("ai_summarization")
    else:
        # Fallback to simple summarization
        result_data["simple_summary"] = _simple_summarize(request.text)
        features_used.append("simple_summarization")
        fallback_used = True
    
    # Try ML embeddings
    embeddings = await _try_ml_embeddings(request.text)
    if embeddings:
        result_data["embeddings"] = embeddings
        features_used.append("ml_embeddings")
    else:
        # Fallback to hash-based embeddings
        result_data["hash_embeddings"] = _simple_embeddings(request.text)
        features_used.append("hash_embeddings")
        fallback_used = True
    
    # Language detection (always available)
    result_data["language_info"] = _detect_language_simple(request.text)
    features_used.append("language_detection")
    
    processing_time = (time.time() - start_time) * 1000
    
    return ProcessingResult(
        original_text=request.text,
        processed_data=result_data,
        features_used=features_used,
        processing_time_ms=processing_time,
        fallback_used=fallback_used
    )


@optional_feature("ai_summarizer")
async def _try_ai_summarization(ai_client, text: str) -> Optional[str]:
    """Try AI summarization if available"""
    if not ai_client:
        return None
    
    try:
        # Simplified AI call (would need proper implementation)
        # This is a placeholder showing the pattern
        logger.info("🤖 Using AI summarization")
        return f"AI Summary: {text[:100]}..." if len(text) > 100 else f"AI Summary: {text}"
    except Exception as e:
        logger.warning("AI summarization failed", error=str(e))
        return None


@optional_feature("ml_embedder")
async def _try_ml_embeddings(embedder, text: str) -> Optional[List[float]]:
    """Try ML embeddings if available"""
    if not embedder:
        return None
    
    try:
        logger.info("🧠 Using ML embeddings")
        # Placeholder for actual embedding generation
        return [0.1, 0.2, 0.3, 0.4, 0.5]  # Mock embedding
    except Exception as e:
        logger.warning("ML embeddings failed", error=str(e))
        return None


def _simple_summarize(text: str) -> str:
    """Simple text summarization - always available"""
    if len(text) <= 200:
        return text
    
    # Find good truncation point
    truncated = text[:200]
    for boundary in ['。', '！', '？', '.', '!', '?']:
        pos = truncated.rfind(boundary)
        if pos > 100:
            return text[:pos + 1]
    
    return text[:197] + "..."


def _simple_embeddings(text: str) -> List[float]:
    """Hash-based embeddings - always available"""
    import hashlib
    
    hash_val = hashlib.md5(text.encode()).hexdigest()
    # Convert first 16 hex chars to 8 float values
    return [
        float(int(hash_val[i:i+2], 16)) / 255.0 
        for i in range(0, 16, 2)
    ]


def _detect_language_simple(text: str) -> Dict[str, Any]:
    """Simple language detection - always available"""
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    english_chars = sum(1 for char in text if char.isascii() and char.isalpha())
    total_chars = len(text)
    
    if total_chars == 0:
        return {"primary": "unknown", "confidence": 0.0}
    
    chinese_ratio = chinese_chars / total_chars
    english_ratio = english_chars / total_chars
    
    if chinese_ratio > 0.3:
        return {"primary": "chinese", "confidence": chinese_ratio}
    elif english_ratio > 0.5:
        return {"primary": "english", "confidence": english_ratio}
    else:
        return {"primary": "mixed", "confidence": max(chinese_ratio, english_ratio)}


@router.get("/features/benchmark")
async def benchmark_features():
    """Benchmark available features"""
    manager = get_feature_manager()
    
    benchmark_results = {}
    test_text = "这是一个测试文本，用于性能基准测试。" * 10
    
    # Test each available feature
    for feature_name in manager.features:
        feature = manager.get_feature(feature_name)
        if feature:
            start_time = time.time()
            
            try:
                if feature_name == "ai_summarizer" and hasattr(feature, 'summarize'):
                    result = feature.summarize(test_text)
                elif feature_name == "ml_embedder" and hasattr(feature, 'encode'):
                    result = feature.encode([test_text])
                else:
                    result = "Feature loaded successfully"
                
                execution_time = (time.time() - start_time) * 1000
                benchmark_results[feature_name] = {
                    "available": True,
                    "execution_time_ms": execution_time,
                    "result_length": len(str(result)) if result else 0
                }
                
            except Exception as e:
                benchmark_results[feature_name] = {
                    "available": False,
                    "error": str(e)
                }
        else:
            benchmark_results[feature_name] = {"available": False}
    
    return {
        "benchmark_results": benchmark_results,
        "test_text_length": len(test_text),
        "timestamp": time.time()
    }


@router.post("/features/reload")
async def reload_features():
    """Reload feature detection - useful after installing new dependencies"""
    dep_manager = get_dependency_manager()
    
    # Re-scan environment
    available = dep_manager.scan_environment()
    feature_flags = dep_manager.create_feature_flags()
    
    # Reset feature manager cache
    feature_manager = get_feature_manager()
    for feature in feature_manager.features.values():
        feature._loaded = False
        feature._failed = False
        feature._instance = None
    
    logger.info("🔄 Features reloaded", available_count=sum(available.values()))
    
    return {
        "message": "Features reloaded successfully",
        "available_dependencies": available,
        "feature_flags": feature_flags,
        "reload_timestamp": time.time()
    }