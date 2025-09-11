"""
生产环境配置验证器
确保所有必需的配置项都已正确设置
"""

import os
import re
import secrets
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
import logging
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.settings = get_settings()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_all(self) -> Tuple[List[str], List[str]]:
        """验证所有配置项"""
        self.errors.clear()
        self.warnings.clear()
        
        # 基础配置验证
        self._validate_basic_config()
        
        # 安全配置验证
        self._validate_security_config()
        
        # 数据库配置验证
        self._validate_database_config()
        
        # Redis 配置验证
        self._validate_redis_config()
        
        # API 密钥验证
        self._validate_api_keys()
        
        # 文件系统验证
        self._validate_filesystem()
        
        # 网络配置验证
        self._validate_network_config()
        
        return self.errors, self.warnings
    
    def _validate_basic_config(self):
        """验证基础配置"""
        # 环境配置
        if not self.settings.environment:
            self.errors.append("ENVIRONMENT 未设置")
        elif self.settings.environment not in ["development", "testing", "production"]:
            self.errors.append(f"无效的 ENVIRONMENT 值: {self.settings.environment}")
        
        # 日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.settings.log_level.upper() not in valid_log_levels:
            self.errors.append(f"无效的 LOG_LEVEL 值: {self.settings.log_level}")
        
        # 应用名称
        if not self.settings.app_name:
            self.warnings.append("APP_NAME 未设置，使用默认值")
    
    def _validate_security_config(self):
        """验证安全配置"""
        # SECRET_KEY 验证
        if not self.settings.secret_key:
            self.errors.append("SECRET_KEY 未设置")
        elif self.settings.secret_key == "dev-secret-key-change-in-production":
            if self.settings.environment == "production":
                self.errors.append("生产环境必须更改默认的 SECRET_KEY")
            else:
                self.warnings.append("使用默认的 SECRET_KEY，生产环境需要更改")
        elif len(self.settings.secret_key) < 32:
            self.warnings.append("SECRET_KEY 长度建议至少32位")
        
        # JWT 配置验证
        if not hasattr(self.settings, 'jwt_secret') or not os.getenv('JWT_SECRET'):
            if self.settings.environment == "production":
                self.errors.append("JWT_SECRET 未设置")
            else:
                self.warnings.append("JWT_SECRET 未设置，将使用 SECRET_KEY")
        
        # JWT 过期时间
        if self.settings.jwt_expire_minutes <= 0:
            self.errors.append("JWT_EXPIRE_MINUTES 必须大于0")
        elif self.settings.jwt_expire_minutes > 10080:  # 7天
            self.warnings.append("JWT_EXPIRE_MINUTES 设置过长，可能存在安全风险")
        
        # CORS 配置
        if self.settings.environment == "production":
            if "*" in self.settings.allowed_origins:
                self.errors.append("生产环境不应允许所有来源的跨域请求")
    
    def _validate_database_config(self):
        """验证数据库配置"""
        if not self.settings.database_url:
            self.errors.append("DATABASE_URL 未设置")
            return
        
        try:
            parsed_url = urlparse(self.settings.database_url)
            
            # 检查数据库类型
            if not parsed_url.scheme:
                self.errors.append("DATABASE_URL 格式无效：缺少数据库类型")
            elif parsed_url.scheme not in ["postgresql", "sqlite"]:
                self.warnings.append(f"不常见的数据库类型: {parsed_url.scheme}")
            
            # 检查主机和端口
            if parsed_url.scheme == "postgresql":
                if not parsed_url.hostname:
                    self.errors.append("PostgreSQL DATABASE_URL 缺少主机名")
                if not parsed_url.port and parsed_url.hostname not in ["localhost", "postgres"]:
                    self.warnings.append("PostgreSQL 未指定端口，使用默认端口 5432")
            
            # 检查用户名和密码
            if parsed_url.scheme == "postgresql":
                if not parsed_url.username:
                    self.errors.append("PostgreSQL DATABASE_URL 缺少用户名")
                if not parsed_url.password:
                    self.warnings.append("PostgreSQL DATABASE_URL 缺少密码")
                elif len(parsed_url.password) < 8:
                    self.warnings.append("数据库密码长度建议至少8位")
            
            # 检查数据库名
            if not parsed_url.path or parsed_url.path == "/":
                self.errors.append("DATABASE_URL 缺少数据库名")
                
        except Exception as e:
            self.errors.append(f"DATABASE_URL 格式错误: {str(e)}")
    
    def _validate_redis_config(self):
        """验证 Redis 配置"""
        if not self.settings.redis_url:
            self.warnings.append("REDIS_URL 未设置，缓存功能将不可用")
            return
        
        try:
            parsed_url = urlparse(self.settings.redis_url)
            
            if parsed_url.scheme != "redis":
                self.errors.append(f"REDIS_URL 协议错误，期望 redis://，得到 {parsed_url.scheme}://")
            
            if not parsed_url.hostname:
                self.errors.append("REDIS_URL 缺少主机名")
            
            if not parsed_url.port and parsed_url.hostname not in ["localhost", "redis"]:
                self.warnings.append("Redis 未指定端口，使用默认端口 6379")
                
        except Exception as e:
            self.errors.append(f"REDIS_URL 格式错误: {str(e)}")
    
    def _validate_api_keys(self):
        """验证 API 密钥"""
        # OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            if not openai_key.startswith("sk-"):
                self.warnings.append("OPENAI_API_KEY 格式可能不正确")
            elif len(openai_key) < 40:
                self.warnings.append("OPENAI_API_KEY 长度可能不正确")
        else:
            self.warnings.append("OPENAI_API_KEY 未设置，AI 功能将不可用")
        
        # Anthropic API Key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            if not anthropic_key.startswith("sk-ant-"):
                self.warnings.append("ANTHROPIC_API_KEY 格式可能不正确")
        else:
            self.warnings.append("ANTHROPIC_API_KEY 未设置，Claude 功能将不可用")
    
    def _validate_filesystem(self):
        """验证文件系统配置"""
        # 检查日志目录
        log_dir = Path("logs")
        if not log_dir.exists():
            try:
                log_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                self.errors.append("无法创建日志目录，权限不足")
        
        # 检查磁盘空间
        import shutil
        try:
            _, _, free = shutil.disk_usage(".")
            free_gb = free / (1024 ** 3)
            if free_gb < 1:
                self.warnings.append(f"磁盘剩余空间不足: {free_gb:.2f}GB")
            elif free_gb < 5:
                self.warnings.append(f"磁盘剩余空间较少: {free_gb:.2f}GB")
        except Exception as e:
            self.warnings.append(f"无法检查磁盘空间: {str(e)}")
        
        # 检查临时目录
        temp_dir = Path("/tmp")
        if not temp_dir.exists() or not temp_dir.is_dir():
            self.warnings.append("临时目录 /tmp 不存在或不可访问")
    
    def _validate_network_config(self):
        """验证网络配置"""
        # 检查端口配置
        api_port = os.getenv("API_PORT", "8000")
        try:
            port = int(api_port)
            if port < 1024 and os.getuid() != 0:  # 非 root 用户
                self.warnings.append(f"端口 {port} 需要管理员权限")
            elif port > 65535:
                self.errors.append(f"无效的端口号: {port}")
        except ValueError:
            self.errors.append(f"API_PORT 不是有效的数字: {api_port}")
        
        # 检查前端 URL 配置
        api_url = os.getenv("NEXT_PUBLIC_API_URL")
        if api_url:
            if not api_url.startswith(("http://", "https://")):
                self.warnings.append("NEXT_PUBLIC_API_URL 应该包含协议前缀")
            elif self.settings.environment == "production" and api_url.startswith("http://"):
                self.warnings.append("生产环境建议使用 HTTPS")
    
    def _validate_production_specific(self):
        """验证生产环境特定配置"""
        if self.settings.environment != "production":
            return
        
        # 生产环境必须关闭调试
        if self.settings.debug:
            self.errors.append("生产环境必须关闭 DEBUG 模式")
        
        # 检查敏感信息是否使用默认值
        sensitive_defaults = {
            "POSTGRES_PASSWORD": "changeme",
            "MINIO_ROOT_PASSWORD": "minioadmin",
            "GRAFANA_PASSWORD": "admin"
        }
        
        for key, default_value in sensitive_defaults.items():
            if os.getenv(key) == default_value:
                self.errors.append(f"生产环境必须更改默认的 {key}")
    
    def generate_secure_key(self) -> str:
        """生成安全的密钥"""
        return secrets.token_urlsafe(32)
    
    def suggest_fixes(self) -> List[str]:
        """生成修复建议"""
        suggestions = []
        
        if "SECRET_KEY 未设置" in self.errors:
            key = self.generate_secure_key()
            suggestions.append(f"设置 SECRET_KEY={key}")
        
        if "JWT_SECRET 未设置" in self.errors:
            key = self.generate_secure_key()
            suggestions.append(f"设置 JWT_SECRET={key}")
        
        if any("默认" in error for error in self.errors):
            suggestions.append("更新所有默认密码和密钥")
        
        if "CORS" in str(self.errors):
            suggestions.append("配置具体的允许来源，而不是使用通配符")
        
        return suggestions


def validate_config() -> Dict[str, Any]:
    """验证配置并返回结果"""
    validator = ConfigValidator()
    errors, warnings = validator.validate_all()
    suggestions = validator.suggest_fixes()
    
    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "environment": validator.settings.environment
    }
    
    return result


def check_config_on_startup():
    """启动时检查配置"""
    result = validate_config()
    
    if not result["valid"]:
        logger.error("配置验证失败:")
        for error in result["errors"]:
            logger.error(f"  ❌ {error}")
        
        if result["suggestions"]:
            logger.info("修复建议:")
            for suggestion in result["suggestions"]:
                logger.info(f"  💡 {suggestion}")
        
        if os.getenv("STRICT_CONFIG_VALIDATION", "false").lower() == "true":
            raise ConfigValidationError("配置验证失败，无法启动应用")
    
    if result["warnings"]:
        logger.warning("配置警告:")
        for warning in result["warnings"]:
            logger.warning(f"  ⚠️  {warning}")
    
    logger.info("✅ 配置验证通过")
    return result


# 配置健康检查端点
async def config_health_check():
    """配置健康检查"""
    result = validate_config()
    
    return {
        "config_valid": result["valid"],
        "error_count": len(result["errors"]),
        "warning_count": len(result["warnings"]),
        "environment": result["environment"],
        "timestamp": "now"
    }