"""
本地化和合规服务
支持多语言、多货币、法律合规、支付集成等
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re

import os

try:
    from babel import Locale, dates, numbers
    from babel.core import get_global
except ImportError:
    Locale = dates = numbers = get_global = None

try:
    import pycountry
except ImportError:
    pycountry = None

try:
    import stripe
except ImportError:
    stripe = None

try:
    import requests
except ImportError:
    requests = None

from app.core.global_config import get_global_config, Region, SUPPORTED_CURRENCIES
from app.core.performance_optimizer import cached
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ComplianceFramework(str, Enum):
    """合规框架"""
    GDPR = "gdpr"  # 欧盟通用数据保护条例
    CCPA = "ccpa"  # 加州消费者隐私法案
    PIPEDA = "pipeda"  # 加拿大个人信息保护和电子文件法
    LGPD = "lgpd"  # 巴西通用数据保护法
    PDPA = "pdpa"  # 新加坡个人数据保护法


class PaymentMethod(str, Enum):
    """支付方式"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    SEPA = "sepa"
    SOFORT = "sofort"
    IDEAL = "ideal"


@dataclass
class LocalizationConfig:
    """本地化配置"""
    locale: str
    language: str
    country: str
    currency: str
    timezone: str
    date_format: str
    number_format: str
    rtl: bool = False  # 是否从右到左阅读


@dataclass
class ComplianceRequirement:
    """合规要求"""
    framework: ComplianceFramework
    requires_consent: bool
    data_retention_days: int
    right_to_deletion: bool
    right_to_portability: bool
    breach_notification_hours: int
    dpo_required: bool  # 是否需要数据保护官


@dataclass
class TaxConfiguration:
    """税收配置"""
    country_code: str
    tax_rate: float
    tax_name: str
    tax_inclusive: bool
    reverse_charge: bool = False


class LocalizationService:
    """本地化服务"""
    
    def __init__(self):
        self.config_manager = get_global_config()
        self.locale_configs = self._init_locale_configs()
        self.compliance_rules = self._init_compliance_rules()
        self.tax_configs = self._init_tax_configs()
    
    def _init_locale_configs(self) -> Dict[str, LocalizationConfig]:
        """初始化本地化配置"""
        configs = {}
        
        # 美洲
        configs["en-US"] = LocalizationConfig(
            locale="en_US", language="en", country="US", currency="USD",
            timezone="America/New_York", date_format="%m/%d/%Y", number_format="#,##0.00"
        )
        configs["es-MX"] = LocalizationConfig(
            locale="es_MX", language="es", country="MX", currency="MXN",
            timezone="America/Mexico_City", date_format="%d/%m/%Y", number_format="#,##0.00"
        )
        configs["pt-BR"] = LocalizationConfig(
            locale="pt_BR", language="pt", country="BR", currency="BRL",
            timezone="America/Sao_Paulo", date_format="%d/%m/%Y", number_format="#.##0,00"
        )
        
        # 欧洲
        configs["en-GB"] = LocalizationConfig(
            locale="en_GB", language="en", country="GB", currency="GBP",
            timezone="Europe/London", date_format="%d/%m/%Y", number_format="#,##0.00"
        )
        configs["de-DE"] = LocalizationConfig(
            locale="de_DE", language="de", country="DE", currency="EUR",
            timezone="Europe/Berlin", date_format="%d.%m.%Y", number_format="#.##0,00"
        )
        configs["fr-FR"] = LocalizationConfig(
            locale="fr_FR", language="fr", country="FR", currency="EUR",
            timezone="Europe/Paris", date_format="%d/%m/%Y", number_format="# ##0,00"
        )
        
        # 亚太
        configs["zh-CN"] = LocalizationConfig(
            locale="zh_CN", language="zh-CN", country="CN", currency="CNY",
            timezone="Asia/Shanghai", date_format="%Y年%m月%d日", number_format="#,##0.00"
        )
        configs["ja-JP"] = LocalizationConfig(
            locale="ja_JP", language="ja", country="JP", currency="JPY",
            timezone="Asia/Tokyo", date_format="%Y年%m月%d日", number_format="#,##0"
        )
        configs["ko-KR"] = LocalizationConfig(
            locale="ko_KR", language="ko", country="KR", currency="KRW",
            timezone="Asia/Seoul", date_format="%Y년 %m월 %d일", number_format="#,##0"
        )
        
        return configs
    
    def _init_compliance_rules(self) -> Dict[str, List[ComplianceRequirement]]:
        """初始化合规规则"""
        rules = {}
        
        # 欧盟 GDPR
        gdpr = ComplianceRequirement(
            framework=ComplianceFramework.GDPR,
            requires_consent=True,
            data_retention_days=365,
            right_to_deletion=True,
            right_to_portability=True,
            breach_notification_hours=72,
            dpo_required=True
        )
        
        # 加州 CCPA
        ccpa = ComplianceRequirement(
            framework=ComplianceFramework.CCPA,
            requires_consent=False,
            data_retention_days=730,
            right_to_deletion=True,
            right_to_portability=True,
            breach_notification_hours=24,
            dpo_required=False
        )
        
        # 按地区分配合规要求
        rules["EU"] = [gdpr]
        rules["US"] = [ccpa]
        rules["CA"] = [ComplianceRequirement(
            framework=ComplianceFramework.PIPEDA,
            requires_consent=True,
            data_retention_days=365,
            right_to_deletion=True,
            right_to_portability=False,
            breach_notification_hours=24,
            dpo_required=False
        )]
        
        return rules
    
    def _init_tax_configs(self) -> Dict[str, TaxConfiguration]:
        """初始化税收配置"""
        configs = {}
        
        # 美国各州销售税（简化）
        configs["US"] = TaxConfiguration("US", 0.0875, "Sales Tax", False)  # 平均税率
        configs["CA"] = TaxConfiguration("CA", 0.13, "HST", True)  # 加拿大统一销售税
        configs["GB"] = TaxConfiguration("GB", 0.20, "VAT", True)  # 英国增值税
        configs["DE"] = TaxConfiguration("DE", 0.19, "MwSt", True)  # 德国增值税
        configs["FR"] = TaxConfiguration("FR", 0.20, "TVA", True)  # 法国增值税
        configs["JP"] = TaxConfiguration("JP", 0.10, "消費税", True)  # 日本消费税
        configs["CN"] = TaxConfiguration("CN", 0.13, "增值税", True)  # 中国增值税
        
        return configs
    
    def get_locale_config(self, locale_code: str) -> Optional[LocalizationConfig]:
        """获取本地化配置"""
        return self.locale_configs.get(locale_code)
    
    def detect_locale(self, accept_language: str, country_code: str = None) -> str:
        """检测用户本地化设置"""
        # 解析Accept-Language头
        languages = self._parse_accept_language(accept_language)
        
        # 根据语言和国家匹配最佳本地化
        for lang, _ in languages:
            if country_code:
                locale_key = f"{lang}-{country_code}"
                if locale_key in self.locale_configs:
                    return locale_key
            
            # 尝试默认国家
            for locale_key in self.locale_configs:
                if locale_key.startswith(lang):
                    return locale_key
        
        return "en-US"  # 默认
    
    def _parse_accept_language(self, accept_language: str) -> List[Tuple[str, float]]:
        """解析Accept-Language头"""
        languages = []
        
        for part in accept_language.split(','):
            if ';q=' in part:
                lang, quality = part.strip().split(';q=')
                quality = float(quality)
            else:
                lang = part.strip()
                quality = 1.0
            
            # 提取语言代码
            lang_code = lang.split('-')[0].lower()
            languages.append((lang_code, quality))
        
        # 按质量排序
        languages.sort(key=lambda x: x[1], reverse=True)
        return languages
    
    @cached(ttl=3600, prefix="localization")
    async def localize_content(self, content: Dict[str, Any], locale: str) -> Dict[str, Any]:
        """本地化内容"""
        config = self.get_locale_config(locale)
        if not config:
            return content
        
        localized = content.copy()
        
        # 本地化日期
        if 'published_at' in content:
            localized['published_at_localized'] = self._format_date(
                content['published_at'], config
            )
        
        # 本地化数字
        if 'reading_time' in content:
            localized['reading_time_localized'] = self._format_number(
                content['reading_time'], config
            )
        
        # 本地化货币（如果有价格信息）
        if 'price' in content:
            localized['price_localized'] = self._format_currency(
                content['price'], config
            )
        
        # 翻译内容（如果需要）
        if config.language != 'en' and 'translations' in content:
            translations = content['translations']
            if config.language in translations:
                localized.update(translations[config.language])
        
        return localized
    
    def _format_date(self, date_str: str, config: LocalizationConfig) -> str:
        """格式化日期"""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            locale_obj = Locale.parse(config.locale)
            return dates.format_datetime(dt, locale=locale_obj)
        except Exception as e:
            logger.error(f"Date formatting error: {e}")
            return date_str
    
    def _format_number(self, number: float, config: LocalizationConfig) -> str:
        """格式化数字"""
        try:
            locale_obj = Locale.parse(config.locale)
            return numbers.format_number(number, locale=locale_obj)
        except Exception as e:
            logger.error(f"Number formatting error: {e}")
            return str(number)
    
    def _format_currency(self, amount: float, config: LocalizationConfig) -> str:
        """格式化货币"""
        try:
            locale_obj = Locale.parse(config.locale)
            return numbers.format_currency(amount, config.currency, locale=locale_obj)
        except Exception as e:
            logger.error(f"Currency formatting error: {e}")
            return f"{config.currency} {amount}"


class ComplianceService:
    """合规服务"""
    
    def __init__(self):
        self.localization_service = LocalizationService()
        self.compliance_rules = self.localization_service.compliance_rules
    
    def get_compliance_requirements(self, country_code: str, region: str) -> List[ComplianceRequirement]:
        """获取合规要求"""
        requirements = []
        
        # 基于国家的合规要求
        if country_code in ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", 
                           "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", 
                           "PL", "PT", "RO", "SK", "SI", "ES", "SE"]:
            requirements.extend(self.compliance_rules.get("EU", []))
        elif country_code == "US":
            requirements.extend(self.compliance_rules.get("US", []))
        elif country_code == "CA":
            requirements.extend(self.compliance_rules.get("CA", []))
        
        return requirements
    
    def check_consent_required(self, country_code: str) -> bool:
        """检查是否需要用户同意"""
        requirements = self.get_compliance_requirements(country_code, "")
        return any(req.requires_consent for req in requirements)
    
    def get_data_retention_period(self, country_code: str) -> int:
        """获取数据保留期限"""
        requirements = self.get_compliance_requirements(country_code, "")
        if requirements:
            return min(req.data_retention_days for req in requirements)
        return 365  # 默认1年
    
    async def generate_privacy_policy(self, country_code: str, language: str) -> str:
        """生成隐私政策"""
        requirements = self.get_compliance_requirements(country_code, "")
        
        # 基础隐私政策模板
        policy_sections = []
        
        policy_sections.append(self._get_data_collection_section(language))
        policy_sections.append(self._get_data_usage_section(language))
        
        # GDPR特定条款
        if any(req.framework == ComplianceFramework.GDPR for req in requirements):
            policy_sections.append(self._get_gdpr_rights_section(language))
        
        # CCPA特定条款
        if any(req.framework == ComplianceFramework.CCPA for req in requirements):
            policy_sections.append(self._get_ccpa_rights_section(language))
        
        policy_sections.append(self._get_contact_section(language))
        
        return "\n\n".join(policy_sections)
    
    def _get_data_collection_section(self, language: str) -> str:
        """数据收集条款"""
        templates = {
            "en": "We collect information you provide directly to us, such as when you create an account, subscribe to our service, or contact us for support.",
            "de": "Wir sammeln Informationen, die Sie uns direkt zur Verfügung stellen, z.B. wenn Sie ein Konto erstellen, unseren Service abonnieren oder uns für Support kontaktieren.",
            "fr": "Nous collectons les informations que vous nous fournissez directement, par exemple lorsque vous créez un compte, vous abonnez à notre service ou nous contactez pour obtenir de l'aide.",
            "es": "Recopilamos información que nos proporciona directamente, como cuando crea una cuenta, se suscribe a nuestro servicio o nos contacta para obtener soporte.",
            "zh-CN": "我们收集您直接提供给我们的信息，例如当您创建账户、订阅我们的服务或联系我们寻求支持时。",
            "ja": "アカウントの作成、サービスの購読、サポートへのお問い合わせなど、お客様が直接当社に提供される情報を収集します。"
        }
        return templates.get(language, templates["en"])
    
    def _get_data_usage_section(self, language: str) -> str:
        """数据使用条款"""
        templates = {
            "en": "We use your information to provide, maintain, and improve our services, process transactions, and communicate with you.",
            "de": "Wir verwenden Ihre Informationen, um unsere Services bereitzustellen, zu warten und zu verbessern, Transaktionen zu verarbeiten und mit Ihnen zu kommunizieren.",
            "fr": "Nous utilisons vos informations pour fournir, maintenir et améliorer nos services, traiter les transactions et communiquer avec vous.",
            "es": "Utilizamos su información para proporcionar, mantener y mejorar nuestros servicios, procesar transacciones y comunicarnos con usted.",
            "zh-CN": "我们使用您的信息来提供、维护和改进我们的服务，处理交易并与您沟通。",
            "ja": "お客様の情報は、サービスの提供、維持、改善、取引の処理、およびお客様とのコミュニケーションのために使用されます。"
        }
        return templates.get(language, templates["en"])
    
    def _get_gdpr_rights_section(self, language: str) -> str:
        """GDPR权利条款"""
        templates = {
            "en": "Under GDPR, you have the right to access, rectify, erase, restrict processing, data portability, and object to processing of your personal data.",
            "de": "Unter der DSGVO haben Sie das Recht auf Zugang, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch gegen die Verarbeitung Ihrer personenbezogenen Daten.",
            "fr": "Sous le RGPD, vous avez le droit d'accéder, rectifier, effacer, restreindre le traitement, la portabilité des données et vous opposer au traitement de vos données personnelles."
        }
        return templates.get(language, templates["en"])
    
    def _get_ccpa_rights_section(self, language: str) -> str:
        """CCPA权利条款"""
        templates = {
            "en": "Under CCPA, California residents have the right to know what personal information is collected, delete personal information, and opt-out of the sale of personal information.",
            "es": "Bajo CCPA, los residentes de California tienen el derecho de saber qué información personal se recopila, eliminar información personal y optar por no participar en la venta de información personal."
        }
        return templates.get(language, templates["en"])
    
    def _get_contact_section(self, language: str) -> str:
        """联系方式条款"""
        templates = {
            "en": "If you have any questions about this Privacy Policy, please contact us at privacy@attentionsync.io",
            "de": "Wenn Sie Fragen zu dieser Datenschutzrichtlinie haben, kontaktieren Sie uns bitte unter privacy@attentionsync.io",
            "fr": "Si vous avez des questions concernant cette politique de confidentialité, veuillez nous contacter à privacy@attentionsync.io",
            "es": "Si tiene alguna pregunta sobre esta Política de Privacidad, contáctenos en privacy@attentionsync.io",
            "zh-CN": "如果您对本隐私政策有任何疑问，请通过 privacy@attentionsync.io 联系我们",
            "ja": "このプライバシーポリシーについてご質問がございましたら、privacy@attentionsync.io までお問い合わせください"
        }
        return templates.get(language, templates["en"])


class PaymentService:
    """支付服务"""
    
    def __init__(self):
        self.localization_service = LocalizationService()
        self.stripe_client = None
        self._init_payment_clients()
    
    def _init_payment_clients(self):
        """初始化支付客户端"""
        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if stripe_key:
            stripe.api_key = stripe_key
            self.stripe_client = stripe
    
    def get_supported_payment_methods(self, country_code: str) -> List[PaymentMethod]:
        """获取支持的支付方式"""
        methods = []
        
        # 基于国家的支付方式
        if country_code in ["US", "CA", "GB", "AU"]:
            methods.extend([PaymentMethod.STRIPE, PaymentMethod.PAYPAL, 
                          PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY])
        
        if country_code in ["DE", "NL", "BE", "AT"]:
            methods.extend([PaymentMethod.STRIPE, PaymentMethod.SEPA, 
                          PaymentMethod.SOFORT, PaymentMethod.IDEAL])
        
        if country_code == "CN":
            methods.extend([PaymentMethod.ALIPAY, PaymentMethod.WECHAT_PAY])
        
        return methods
    
    async def calculate_price_with_tax(self, base_price: float, country_code: str, 
                                     currency: str) -> Dict[str, Any]:
        """计算含税价格"""
        tax_config = self.localization_service.tax_configs.get(country_code)
        
        if not tax_config:
            return {
                "base_price": base_price,
                "tax_amount": 0.0,
                "total_price": base_price,
                "currency": currency,
                "tax_inclusive": False
            }
        
        if tax_config.tax_inclusive:
            # 价格已含税
            tax_amount = base_price * tax_config.tax_rate / (1 + tax_config.tax_rate)
            net_price = base_price - tax_amount
        else:
            # 价格不含税
            net_price = base_price
            tax_amount = base_price * tax_config.tax_rate
        
        total_price = net_price + tax_amount
        
        return {
            "base_price": net_price,
            "tax_amount": tax_amount,
            "tax_rate": tax_config.tax_rate,
            "tax_name": tax_config.tax_name,
            "total_price": total_price,
            "currency": currency,
            "tax_inclusive": tax_config.tax_inclusive
        }
    
    async def create_payment_intent(self, amount: float, currency: str, 
                                  country_code: str, payment_method: PaymentMethod) -> Dict[str, Any]:
        """创建支付意图"""
        if payment_method == PaymentMethod.STRIPE and self.stripe_client:
            try:
                intent = await self.stripe_client.PaymentIntent.create_async(
                    amount=int(amount * 100),  # Stripe使用分作为单位
                    currency=currency.lower(),
                    metadata={"country": country_code}
                )
                
                return {
                    "payment_intent_id": intent.id,
                    "client_secret": intent.client_secret,
                    "status": intent.status,
                    "amount": amount,
                    "currency": currency
                }
            except Exception as e:
                logger.error(f"Stripe payment intent creation failed: {e}")
                raise
        
        raise NotImplementedError(f"Payment method {payment_method} not implemented")


# 全局实例
_localization_service = None
_compliance_service = None
_payment_service = None


def get_localization_service() -> LocalizationService:
    """获取本地化服务实例"""
    global _localization_service
    if _localization_service is None:
        _localization_service = LocalizationService()
    return _localization_service


def get_compliance_service() -> ComplianceService:
    """获取合规服务实例"""
    global _compliance_service
    if _compliance_service is None:
        _compliance_service = ComplianceService()
    return _compliance_service


def get_payment_service() -> PaymentService:
    """获取支付服务实例"""
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service