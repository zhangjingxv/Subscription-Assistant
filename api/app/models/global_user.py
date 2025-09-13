"""
全球化用户模型
支持多区域、多语言、合规要求的用户管理
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, Float, 
    Text, JSON, ARRAY, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from app.models.base import BaseModel
from app.core.global_config import Region, ComplianceLevel


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PENDING_VERIFICATION = "pending_verification"


class SubscriptionTier(str, Enum):
    """订阅层级"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class GlobalUser(BaseModel):
    """全球化用户模型"""
    
    __tablename__ = "global_users"
    
    # 基础字段
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # 用户状态
    status = Column(String(50), default=UserStatus.PENDING_VERIFICATION, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 全球化字段
    preferred_language = Column(String(10), default="en", nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    country_code = Column(String(3), nullable=True, index=True)
    region = Column(String(50), default="global", nullable=False, index=True)
    currency = Column(String(3), default="USD", nullable=False)
    
    # 个人信息
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    display_name = Column(String(200), nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    
    # 联系信息
    phone_number = Column(String(20), nullable=True)
    phone_verified = Column(Boolean, default=False, nullable=False)
    
    # 个性化设置
    preferences = Column(JSONB, default=dict, nullable=False)
    notification_settings = Column(JSONB, default=dict, nullable=False)
    privacy_settings = Column(JSONB, default=dict, nullable=False)
    ui_settings = Column(JSONB, default=dict, nullable=False)
    
    # 订阅信息
    subscription_tier = Column(String(50), default=SubscriptionTier.FREE, nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)
    
    # 合规字段
    gdpr_consent = Column(Boolean, default=False, nullable=False)
    gdpr_consent_date = Column(DateTime, nullable=True)
    marketing_consent = Column(Boolean, default=False, nullable=False)
    cookie_consent = Column(Boolean, default=False, nullable=False)
    data_retention_days = Column(Integer, default=365, nullable=False)
    
    # 使用统计
    login_count = Column(Integer, default=0, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(INET, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    
    # 安全字段
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(255), nullable=True)
    recovery_codes = Column(ARRAY(String), nullable=True)
    
    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    # 元数据
    metadata = Column(JSONB, default=dict, nullable=False)
    tags = Column(ARRAY(String), default=list, nullable=False)
    
    # 索引
    __table_args__ = (
        # 唯一约束（排除软删除的记录）
        UniqueConstraint('email', name='uq_users_email_not_deleted', 
                        postgresql_where=Column('deleted_at').is_(None)),
        UniqueConstraint('username', name='uq_users_username_not_deleted',
                        postgresql_where=Column('deleted_at').is_(None)),
        
        # 复合索引
        Index('ix_users_region_status', 'region', 'status'),
        Index('ix_users_country_language', 'country_code', 'preferred_language'),
        Index('ix_users_subscription', 'subscription_tier', 'subscription_expires_at'),
        Index('ix_users_activity', 'last_activity_at', 'status'),
        
        # 检查约束
        CheckConstraint('email ~* \'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$\'', 
                       name='check_email_format'),
        CheckConstraint('data_retention_days > 0', name='check_retention_days'),
        CheckConstraint('failed_login_attempts >= 0', name='check_failed_attempts'),
    )
    
    @validates('email')
    def validate_email(self, key, email):
        """验证邮箱格式"""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")
        return email.lower().strip()
    
    @validates('preferred_language')
    def validate_language(self, key, language):
        """验证语言代码"""
        supported_languages = ["en", "zh-CN", "de", "fr", "es", "ja"]
        if language not in supported_languages:
            return "en"  # 默认英语
        return language
    
    @validates('region')
    def validate_region(self, key, region):
        """验证区域"""
        valid_regions = [r.value for r in Region]
        if region not in valid_regions:
            return Region.GLOBAL.value
        return region
    
    @hybrid_property
    def full_name(self) -> Optional[str]:
        """完整姓名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.display_name or self.username
    
    @hybrid_property
    def is_premium(self) -> bool:
        """是否为付费用户"""
        return self.subscription_tier in [SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE]
    
    @hybrid_property
    def is_subscription_active(self) -> bool:
        """订阅是否有效"""
        if self.subscription_tier == SubscriptionTier.FREE:
            return True
        if not self.subscription_expires_at:
            return False
        return self.subscription_expires_at > datetime.utcnow()
    
    @hybrid_property
    def is_locked(self) -> bool:
        """账户是否被锁定"""
        if not self.locked_until:
            return False
        return self.locked_until > datetime.utcnow()
    
    @hybrid_property
    def requires_gdpr_compliance(self) -> bool:
        """是否需要GDPR合规"""
        eu_countries = ["DE", "FR", "ES", "IT", "NL", "BE", "AT", "SE", "DK", "FI", "IE", "PT", "GR", "CZ", "HU", "PL", "SK", "SI", "EE", "LV", "LT", "LU", "MT", "CY", "BG", "RO", "HR"]
        return self.country_code in eu_countries or self.region == Region.EUROPE.value
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取用户偏好设置"""
        return self.preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any) -> None:
        """设置用户偏好"""
        if not self.preferences:
            self.preferences = {}
        self.preferences[key] = value
    
    def get_notification_setting(self, key: str, default: bool = True) -> bool:
        """获取通知设置"""
        return self.notification_settings.get(key, default)
    
    def set_notification_setting(self, key: str, value: bool) -> None:
        """设置通知偏好"""
        if not self.notification_settings:
            self.notification_settings = {}
        self.notification_settings[key] = value
    
    def increment_login_count(self, ip_address: str = None) -> None:
        """增加登录次数"""
        self.login_count += 1
        self.last_login_at = datetime.utcnow()
        self.last_activity_at = datetime.utcnow()
        if ip_address:
            self.last_login_ip = ip_address
        self.failed_login_attempts = 0  # 重置失败次数
    
    def increment_failed_login(self, max_attempts: int = 5, lockout_duration: int = 30) -> None:
        """增加失败登录次数"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_duration)
    
    def unlock_account(self) -> None:
        """解锁账户"""
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def soft_delete(self) -> None:
        """软删除用户"""
        self.deleted_at = datetime.utcnow()
        self.status = UserStatus.DELETED
        self.is_active = False
        # 清理敏感信息
        self.email = f"deleted_{self.id}@deleted.local"
        self.password_hash = ""
        self.phone_number = None
        self.two_factor_secret = None
        self.recovery_codes = None
    
    def can_be_deleted(self) -> bool:
        """检查是否可以删除"""
        if self.requires_gdpr_compliance and self.gdpr_consent:
            return True
        
        # 检查数据保留期
        retention_date = self.created_at + timedelta(days=self.data_retention_days)
        return datetime.utcnow() > retention_date
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "id": str(self.id),
            "email": self.email if include_sensitive else self.email.split('@')[0] + "@***",
            "username": self.username,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "preferred_language": self.preferred_language,
            "timezone": self.timezone,
            "country_code": self.country_code,
            "region": self.region,
            "currency": self.currency,
            "subscription_tier": self.subscription_tier,
            "is_premium": self.is_premium,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        
        if include_sensitive:
            data.update({
                "phone_number": self.phone_number,
                "preferences": self.preferences,
                "notification_settings": self.notification_settings,
                "privacy_settings": self.privacy_settings,
                "gdpr_consent": self.gdpr_consent,
                "marketing_consent": self.marketing_consent,
            })
        
        return data
    
    def __repr__(self) -> str:
        return f"<GlobalUser {self.email} ({self.region})>"