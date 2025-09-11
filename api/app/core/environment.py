"""
环境管理和配置热重载
支持不同环境的配置管理和运行时配置更新
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from functools import lru_cache
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self):
        self.current_env = os.getenv("ENVIRONMENT", "development")
        self.config_cache = {}
        self.last_reload = datetime.now()
        self._env_configs = {}
        self._load_environment_configs()
    
    def _load_environment_configs(self):
        """加载不同环境的配置"""
        env_files = {
            "development": ".env.development",
            "testing": ".env.testing", 
            "production": ".env.production"
        }
        
        for env, filename in env_files.items():
            config_path = Path(filename)
            if config_path.exists():
                self._env_configs[env] = self._load_env_file(config_path)
            else:
                logger.warning(f"Environment config file not found: {filename}")
                self._env_configs[env] = {}
    
    def _load_env_file(self, file_path: Path) -> Dict[str, str]:
        """加载环境文件"""
        config = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # 移除引号
                        value = value.strip('"\'')
                        config[key.strip()] = value
        except Exception as e:
            logger.error(f"Failed to load env file {file_path}: {e}")
        
        return config
    
    def get_environment(self) -> str:
        """获取当前环境"""
        return self.current_env
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.current_env == "development"
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.current_env == "testing"
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.current_env == "production"
    
    def get_config_value(self, key: str, default: Any = None, env: str = None) -> Any:
        """获取配置值"""
        # 优先从环境变量获取
        if key in os.environ:
            return os.environ[key]
        
        # 从指定环境配置获取
        target_env = env or self.current_env
        if target_env in self._env_configs and key in self._env_configs[target_env]:
            return self._env_configs[target_env][key]
        
        return default
    
    def set_config_value(self, key: str, value: str, persist: bool = False):
        """设置配置值"""
        # 设置到环境变量
        os.environ[key] = value
        
        # 可选择持久化到配置文件
        if persist:
            self._persist_config_value(key, value)
        
        # 清除缓存
        self.config_cache.clear()
    
    def _persist_config_value(self, key: str, value: str):
        """持久化配置值到文件"""
        env_file = f".env.{self.current_env}"
        env_path = Path(env_file)
        
        # 读取现有配置
        lines = []
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 更新或添加配置项
        key_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                key_found = True
                break
        
        if not key_found:
            lines.append(f"{key}={value}\n")
        
        # 写回文件
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            logger.info(f"Config value persisted: {key}")
        except Exception as e:
            logger.error(f"Failed to persist config: {e}")
    
    def reload_config(self):
        """重新加载配置"""
        self._load_environment_configs()
        self.config_cache.clear()
        self.last_reload = datetime.now()
        logger.info("Configuration reloaded")
    
    def get_all_config(self, include_secrets: bool = False) -> Dict[str, Any]:
        """获取所有配置"""
        config = {}
        
        # 从环境配置文件获取
        if self.current_env in self._env_configs:
            config.update(self._env_configs[self.current_env])
        
        # 从环境变量获取（会覆盖文件配置）
        for key, value in os.environ.items():
            config[key] = value
        
        # 过滤敏感信息
        if not include_secrets:
            sensitive_keys = [
                'SECRET_KEY', 'JWT_SECRET', 'DATABASE_URL', 'REDIS_URL',
                'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'POSTGRES_PASSWORD',
                'MINIO_ROOT_PASSWORD', 'GRAFANA_PASSWORD'
            ]
            for key in sensitive_keys:
                if key in config:
                    config[key] = "***HIDDEN***"
        
        return config
    
    def validate_environment(self) -> Dict[str, Any]:
        """验证当前环境配置"""
        from app.core.config_validator import validate_config
        return validate_config()
    
    def switch_environment(self, new_env: str):
        """切换环境（仅用于测试）"""
        if new_env not in ["development", "testing", "production"]:
            raise ValueError(f"Invalid environment: {new_env}")
        
        old_env = self.current_env
        self.current_env = new_env
        os.environ["ENVIRONMENT"] = new_env
        self.reload_config()
        
        logger.info(f"Environment switched from {old_env} to {new_env}")


# 全局环境管理器实例
env_manager = EnvironmentManager()


# 环境特定的功能开关
class FeatureFlags:
    """功能开关管理"""
    
    def __init__(self):
        self.flags = self._load_feature_flags()
    
    def _load_feature_flags(self) -> Dict[str, bool]:
        """加载功能开关配置"""
        flags_file = Path(f"feature_flags_{env_manager.get_environment()}.json")
        
        if flags_file.exists():
            try:
                with open(flags_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load feature flags: {e}")
        
        # 默认功能开关
        return {
            "ai_summarization": env_manager.is_production(),
            "content_clustering": True,
            "user_analytics": env_manager.is_production(),
            "debug_mode": env_manager.is_development(),
            "performance_monitoring": True,
            "experimental_features": env_manager.is_development(),
        }
    
    def is_enabled(self, flag_name: str) -> bool:
        """检查功能是否启用"""
        # 优先从环境变量检查
        env_flag = os.getenv(f"FEATURE_{flag_name.upper()}")
        if env_flag is not None:
            return env_flag.lower() in ("true", "1", "yes", "on")
        
        return self.flags.get(flag_name, False)
    
    def enable_feature(self, flag_name: str):
        """启用功能"""
        self.flags[flag_name] = True
        self._save_feature_flags()
    
    def disable_feature(self, flag_name: str):
        """禁用功能"""
        self.flags[flag_name] = False
        self._save_feature_flags()
    
    def _save_feature_flags(self):
        """保存功能开关配置"""
        flags_file = Path(f"feature_flags_{env_manager.get_environment()}.json")
        
        try:
            with open(flags_file, 'w', encoding='utf-8') as f:
                json.dump(self.flags, f, indent=2, ensure_ascii=False)
            logger.info("Feature flags saved")
        except Exception as e:
            logger.error(f"Failed to save feature flags: {e}")
    
    def get_all_flags(self) -> Dict[str, bool]:
        """获取所有功能开关状态"""
        return self.flags.copy()


# 全局功能开关实例
feature_flags = FeatureFlags()


# 配置缓存装饰器
def cached_config(ttl_seconds: int = 300):
    """配置缓存装饰器"""
    def decorator(func):
        cache_key = f"config_cache_{func.__name__}"
        
        def wrapper(*args, **kwargs):
            now = datetime.now()
            
            # 检查缓存
            if cache_key in env_manager.config_cache:
                cached_data, cached_time = env_manager.config_cache[cache_key]
                if (now - cached_time).total_seconds() < ttl_seconds:
                    return cached_data
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            env_manager.config_cache[cache_key] = (result, now)
            
            return result
        
        return wrapper
    return decorator


# 环境特定的配置获取函数
@cached_config(ttl_seconds=60)
def get_database_config() -> Dict[str, Any]:
    """获取数据库配置"""
    return {
        "url": env_manager.get_config_value("DATABASE_URL"),
        "pool_size": int(env_manager.get_config_value("DB_POOL_SIZE", "20")),
        "max_overflow": int(env_manager.get_config_value("DB_MAX_OVERFLOW", "30")),
        "pool_timeout": int(env_manager.get_config_value("DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(env_manager.get_config_value("DB_POOL_RECYCLE", "3600")),
    }


@cached_config(ttl_seconds=60)
def get_redis_config() -> Dict[str, Any]:
    """获取 Redis 配置"""
    return {
        "url": env_manager.get_config_value("REDIS_URL"),
        "max_connections": int(env_manager.get_config_value("REDIS_MAX_CONNECTIONS", "100")),
        "retry_on_timeout": env_manager.get_config_value("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true",
        "socket_keepalive": env_manager.get_config_value("REDIS_SOCKET_KEEPALIVE", "true").lower() == "true",
    }


@cached_config(ttl_seconds=300)
def get_ai_config() -> Dict[str, Any]:
    """获取 AI 服务配置"""
    return {
        "openai_api_key": env_manager.get_config_value("OPENAI_API_KEY"),
        "anthropic_api_key": env_manager.get_config_value("ANTHROPIC_API_KEY"),
        "default_model": env_manager.get_config_value("DEFAULT_AI_MODEL", "gpt-3.5-turbo"),
        "max_tokens": int(env_manager.get_config_value("AI_MAX_TOKENS", "2000")),
        "temperature": float(env_manager.get_config_value("AI_TEMPERATURE", "0.7")),
    }


# 配置热重载端点
async def reload_config_endpoint():
    """配置热重载端点"""
    try:
        env_manager.reload_config()
        feature_flags.flags = feature_flags._load_feature_flags()
        
        return {
            "status": "success",
            "message": "Configuration reloaded",
            "timestamp": datetime.now().isoformat(),
            "environment": env_manager.get_environment()
        }
    except Exception as e:
        logger.error(f"Failed to reload config: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


# 配置信息端点
async def config_info_endpoint():
    """配置信息端点"""
    return {
        "environment": env_manager.get_environment(),
        "last_reload": env_manager.last_reload.isoformat(),
        "feature_flags": feature_flags.get_all_flags(),
        "config_validation": env_manager.validate_environment(),
    }