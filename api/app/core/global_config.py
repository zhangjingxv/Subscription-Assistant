"""
全球化配置管理
支持多区域、多语言、多货币的配置体系
"""

import os
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Region(str, Enum):
    """支持的区域"""
    AMERICAS = "americas"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    GLOBAL = "global"


class ComplianceLevel(str, Enum):
    """合规级别"""
    BASIC = "basic"
    ENHANCED = "enhanced"
    STRICT = "strict"


@dataclass
class CurrencyConfig:
    """货币配置"""
    code: str
    symbol: str
    decimal_places: int = 2
    is_crypto: bool = False


@dataclass
class PaymentProvider:
    """支付提供商配置"""
    name: str
    regions: List[Region]
    currencies: List[str]
    api_endpoint: str
    is_active: bool = True


class RegionalSettings(BaseModel):
    """区域特定设置"""
    region: Region
    primary_language: str = "en"
    supported_languages: List[str] = Field(default_factory=lambda: ["en"])
    timezone: str = "UTC"
    currency: str = "USD"
    
    # 合规设置
    compliance_level: ComplianceLevel = ComplianceLevel.BASIC
    data_retention_days: int = 365
    requires_gdpr_consent: bool = False
    requires_cookie_consent: bool = False
    
    # 性能设置
    cdn_region: str = "global"
    cache_ttl_seconds: int = 3600
    rate_limit_per_minute: int = 1000
    
    # 支付设置
    supported_payment_methods: List[str] = Field(default_factory=list)
    tax_calculation_enabled: bool = False


class GlobalSettings(BaseSettings):
    """全球化应用设置"""
    
    # 基础设置
    app_name: str = "AttentionSync"
    version: str = "2.0.0"
    environment: str = "production"
    
    # 全球化设置
    default_region: Region = Region.GLOBAL
    supported_regions: List[Region] = Field(
        default_factory=lambda: [Region.AMERICAS, Region.EUROPE, Region.ASIA_PACIFIC]
    )
    
    # 多语言设置
    default_language: str = "en"
    supported_languages: List[str] = Field(
        default_factory=lambda: ["en", "zh-CN", "de", "fr", "es", "ja"]
    )
    
    # AI服务配置
    ai_service_regions: Dict[str, str] = Field(
        default_factory=lambda: {
            "americas": "us-east-1",
            "europe": "eu-west-1", 
            "asia_pacific": "ap-southeast-1"
        }
    )
    
    # 数据库配置
    database_regions: Dict[str, str] = Field(
        default_factory=lambda: {
            "americas": os.getenv("DB_AMERICAS_URL", ""),
            "europe": os.getenv("DB_EUROPE_URL", ""),
            "asia_pacific": os.getenv("DB_ASIA_URL", "")
        }
    )
    
    # 缓存配置
    redis_clusters: Dict[str, str] = Field(
        default_factory=lambda: {
            "americas": os.getenv("REDIS_AMERICAS_URL", "redis://localhost:6379/0"),
            "europe": os.getenv("REDIS_EUROPE_URL", "redis://localhost:6379/1"),
            "asia_pacific": os.getenv("REDIS_ASIA_URL", "redis://localhost:6379/2")
        }
    )
    
    # 安全设置
    jwt_secrets: Dict[str, str] = Field(
        default_factory=lambda: {
            "americas": os.getenv("JWT_SECRET_AMERICAS", "change-me"),
            "europe": os.getenv("JWT_SECRET_EUROPE", "change-me"),
            "asia_pacific": os.getenv("JWT_SECRET_ASIA", "change-me")
        }
    )
    
    # CDN配置
    cdn_endpoints: Dict[str, str] = Field(
        default_factory=lambda: {
            "global": os.getenv("CDN_GLOBAL", "https://cdn.attentionsync.io"),
            "americas": os.getenv("CDN_AMERICAS", "https://americas.cdn.attentionsync.io"),
            "europe": os.getenv("CDN_EUROPE", "https://europe.cdn.attentionsync.io"),
            "asia_pacific": os.getenv("CDN_ASIA", "https://asia.cdn.attentionsync.io")
        }
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 区域特定配置
REGIONAL_CONFIGS: Dict[Region, RegionalSettings] = {
    Region.AMERICAS: RegionalSettings(
        region=Region.AMERICAS,
        primary_language="en",
        supported_languages=["en", "es", "fr"],
        timezone="America/New_York",
        currency="USD",
        compliance_level=ComplianceLevel.ENHANCED,
        data_retention_days=2555,  # 7 years for financial data
        requires_gdpr_consent=False,
        requires_cookie_consent=True,
        cdn_region="americas",
        cache_ttl_seconds=1800,
        rate_limit_per_minute=2000,
        supported_payment_methods=["stripe", "paypal", "apple_pay", "google_pay"],
        tax_calculation_enabled=True
    ),
    
    Region.EUROPE: RegionalSettings(
        region=Region.EUROPE,
        primary_language="en",
        supported_languages=["en", "de", "fr", "es"],
        timezone="Europe/London",
        currency="EUR",
        compliance_level=ComplianceLevel.STRICT,
        data_retention_days=365,
        requires_gdpr_consent=True,
        requires_cookie_consent=True,
        cdn_region="europe",
        cache_ttl_seconds=3600,
        rate_limit_per_minute=1500,
        supported_payment_methods=["stripe", "sepa", "sofort", "ideal"],
        tax_calculation_enabled=True
    ),
    
    Region.ASIA_PACIFIC: RegionalSettings(
        region=Region.ASIA_PACIFIC,
        primary_language="en",
        supported_languages=["en", "zh-CN", "ja"],
        timezone="Asia/Singapore",
        currency="USD",
        compliance_level=ComplianceLevel.BASIC,
        data_retention_days=1095,  # 3 years
        requires_gdpr_consent=False,
        requires_cookie_consent=False,
        cdn_region="asia_pacific",
        cache_ttl_seconds=1800,
        rate_limit_per_minute=3000,
        supported_payment_methods=["stripe", "alipay", "wechat_pay"],
        tax_calculation_enabled=False
    )
}

# 货币配置
SUPPORTED_CURRENCIES: Dict[str, CurrencyConfig] = {
    "USD": CurrencyConfig("USD", "$", 2),
    "EUR": CurrencyConfig("EUR", "€", 2),
    "GBP": CurrencyConfig("GBP", "£", 2),
    "JPY": CurrencyConfig("JPY", "¥", 0),
    "CNY": CurrencyConfig("CNY", "¥", 2),
    "CAD": CurrencyConfig("CAD", "C$", 2),
    "AUD": CurrencyConfig("AUD", "A$", 2),
}

# 支付提供商配置
PAYMENT_PROVIDERS: List[PaymentProvider] = [
    PaymentProvider(
        name="stripe",
        regions=[Region.AMERICAS, Region.EUROPE, Region.ASIA_PACIFIC],
        currencies=["USD", "EUR", "GBP", "CAD", "AUD"],
        api_endpoint="https://api.stripe.com/v1"
    ),
    PaymentProvider(
        name="paypal",
        regions=[Region.AMERICAS, Region.EUROPE],
        currencies=["USD", "EUR", "GBP", "CAD"],
        api_endpoint="https://api.paypal.com/v2"
    ),
    PaymentProvider(
        name="alipay",
        regions=[Region.ASIA_PACIFIC],
        currencies=["USD", "CNY"],
        api_endpoint="https://openapi.alipay.com/gateway.do"
    ),
    PaymentProvider(
        name="wechat_pay",
        regions=[Region.ASIA_PACIFIC],
        currencies=["USD", "CNY"],
        api_endpoint="https://api.mch.weixin.qq.com/v3"
    )
]


class GlobalConfigManager:
    """全球化配置管理器"""
    
    def __init__(self):
        self.settings = GlobalSettings()
        self.regional_configs = REGIONAL_CONFIGS
        self.currencies = SUPPORTED_CURRENCIES
        self.payment_providers = PAYMENT_PROVIDERS
    
    def get_regional_config(self, region: Region) -> RegionalSettings:
        """获取区域配置"""
        return self.regional_configs.get(region, self.regional_configs[Region.GLOBAL])
    
    def get_user_region(self, ip_address: str, accept_language: str = None) -> Region:
        """根据IP和语言确定用户区域"""
        # 简化实现，实际应该使用GeoIP服务
        if accept_language:
            if "zh" in accept_language.lower():
                return Region.ASIA_PACIFIC
            elif any(lang in accept_language.lower() for lang in ["de", "fr", "it", "es"]):
                return Region.EUROPE
        
        # 默认返回美洲区域
        return Region.AMERICAS
    
    def get_database_url(self, region: Region) -> str:
        """获取区域数据库URL"""
        return self.settings.database_regions.get(region.value, self.settings.database_url)
    
    def get_redis_url(self, region: Region) -> str:
        """获取区域Redis URL"""
        return self.settings.redis_clusters.get(region.value, "redis://localhost:6379/0")
    
    def get_jwt_secret(self, region: Region) -> str:
        """获取区域JWT密钥"""
        return self.settings.jwt_secrets.get(region.value, "change-me-in-production")
    
    def get_cdn_endpoint(self, region: Region) -> str:
        """获取CDN端点"""
        return self.settings.cdn_endpoints.get(region.value, self.settings.cdn_endpoints["global"])
    
    def get_supported_payment_methods(self, region: Region, currency: str) -> List[str]:
        """获取支持的支付方式"""
        regional_config = self.get_regional_config(region)
        supported_methods = []
        
        for provider in self.payment_providers:
            if (region in provider.regions and 
                currency in provider.currencies and 
                provider.name in regional_config.supported_payment_methods):
                supported_methods.append(provider.name)
        
        return supported_methods
    
    def is_feature_enabled(self, feature: str, region: Region) -> bool:
        """检查功能是否在特定区域启用"""
        regional_config = self.get_regional_config(region)
        
        # 基于合规级别的功能控制
        if feature == "advanced_analytics":
            return regional_config.compliance_level != ComplianceLevel.STRICT
        elif feature == "social_login":
            return regional_config.compliance_level == ComplianceLevel.BASIC
        elif feature == "data_export":
            return regional_config.requires_gdpr_consent
        
        return True


@lru_cache()
def get_global_config() -> GlobalConfigManager:
    """获取全局配置管理器实例"""
    return GlobalConfigManager()


# 便捷函数
def get_user_config(ip_address: str, accept_language: str = None) -> tuple[Region, RegionalSettings]:
    """获取用户配置"""
    config_manager = get_global_config()
    region = config_manager.get_user_region(ip_address, accept_language)
    regional_config = config_manager.get_regional_config(region)
    return region, regional_config