'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';

// 全球化配置接口
interface GlobalizationConfig {
  region: string;
  locale: string;
  language: string;
  country: string;
  currency: string;
  timezone: string;
  rtl: boolean;
}

// 性能指标接口
interface PerformanceMetrics {
  responseTime: number;
  cacheHitRate: number;
  region: string;
  cdnStatus: string;
}

// 合规设置接口
interface ComplianceSettings {
  gdprRequired: boolean;
  cookieConsentRequired: boolean;
  dataRetentionDays: number;
  privacyPolicyUrl: string;
}

// 全球化上下文接口
interface GlobalizationContextType {
  config: GlobalizationConfig;
  metrics: PerformanceMetrics;
  compliance: ComplianceSettings;
  updateConfig: (updates: Partial<GlobalizationConfig>) => void;
  formatCurrency: (amount: number) => string;
  formatDate: (date: Date) => string;
  formatNumber: (number: number) => string;
  detectUserRegion: () => Promise<string>;
  isFeatureEnabled: (feature: string) => boolean;
}

// 创建上下文
const GlobalizationContext = createContext<GlobalizationContextType | undefined>(undefined);

// 默认配置
const defaultConfig: GlobalizationConfig = {
  region: 'global',
  locale: 'en-US',
  language: 'en',
  country: 'US',
  currency: 'USD',
  timezone: 'UTC',
  rtl: false,
};

const defaultMetrics: PerformanceMetrics = {
  responseTime: 0,
  cacheHitRate: 0,
  region: 'global',
  cdnStatus: 'unknown',
};

const defaultCompliance: ComplianceSettings = {
  gdprRequired: false,
  cookieConsentRequired: false,
  dataRetentionDays: 365,
  privacyPolicyUrl: '/privacy',
};

// 区域检测函数
async function detectUserRegion(): Promise<string> {
  try {
    // 1. 尝试从Cloudflare头部获取
    const cfCountry = document.querySelector('meta[name="cf-country"]')?.getAttribute('content');
    if (cfCountry) {
      return mapCountryToRegion(cfCountry);
    }

    // 2. 使用浏览器语言偏好
    const languages = navigator.languages || [navigator.language];
    for (const lang of languages) {
      const region = mapLanguageToRegion(lang);
      if (region !== 'global') {
        return region;
      }
    }

    // 3. 使用时区信息
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return mapTimezoneToRegion(timezone);

  } catch (error) {
    console.warn('Failed to detect user region:', error);
    return 'global';
  }
}

// 国家到区域映射
function mapCountryToRegion(country: string): string {
  const countryToRegion: { [key: string]: string } = {
    // 美洲
    'US': 'americas', 'CA': 'americas', 'MX': 'americas', 'BR': 'americas',
    'AR': 'americas', 'CL': 'americas', 'CO': 'americas', 'PE': 'americas',
    
    // 欧洲
    'DE': 'europe', 'FR': 'europe', 'ES': 'europe', 'IT': 'europe',
    'GB': 'europe', 'NL': 'europe', 'BE': 'europe', 'AT': 'europe',
    'SE': 'europe', 'DK': 'europe', 'FI': 'europe', 'NO': 'europe',
    'PL': 'europe', 'CZ': 'europe', 'HU': 'europe', 'PT': 'europe',
    
    // 亚太
    'CN': 'asia_pacific', 'JP': 'asia_pacific', 'KR': 'asia_pacific',
    'SG': 'asia_pacific', 'AU': 'asia_pacific', 'NZ': 'asia_pacific',
    'IN': 'asia_pacific', 'TH': 'asia_pacific', 'MY': 'asia_pacific',
    'PH': 'asia_pacific', 'ID': 'asia_pacific', 'VN': 'asia_pacific',
  };

  return countryToRegion[country.toUpperCase()] || 'global';
}

// 语言到区域映射
function mapLanguageToRegion(language: string): string {
  const lang = language.split('-')[0].toLowerCase();
  
  const languageToRegion: { [key: string]: string } = {
    'en': 'americas',  // 默认英语到美洲
    'es': 'americas',  // 西班牙语到美洲
    'pt': 'americas',  // 葡萄牙语到美洲
    'fr': 'americas',  // 法语到美洲（加拿大）
    
    'de': 'europe',    // 德语到欧洲
    'it': 'europe',    // 意大利语到欧洲
    'nl': 'europe',    // 荷兰语到欧洲
    'sv': 'europe',    // 瑞典语到欧洲
    'da': 'europe',    // 丹麦语到欧洲
    'fi': 'europe',    // 芬兰语到欧洲
    'no': 'europe',    // 挪威语到欧洲
    'pl': 'europe',    // 波兰语到欧洲
    'cs': 'europe',    // 捷克语到欧洲
    'hu': 'europe',    // 匈牙利语到欧洲
    
    'zh': 'asia_pacific', // 中文到亚太
    'ja': 'asia_pacific', // 日语到亚太
    'ko': 'asia_pacific', // 韩语到亚太
    'th': 'asia_pacific', // 泰语到亚太
    'vi': 'asia_pacific', // 越南语到亚太
    'hi': 'asia_pacific', // 印地语到亚太
    'ms': 'asia_pacific', // 马来语到亚太
  };

  return languageToRegion[lang] || 'global';
}

// 时区到区域映射
function mapTimezoneToRegion(timezone: string): string {
  if (timezone.includes('America/')) return 'americas';
  if (timezone.includes('Europe/')) return 'europe';
  if (timezone.includes('Asia/') || timezone.includes('Australia/') || timezone.includes('Pacific/')) {
    return 'asia_pacific';
  }
  return 'global';
}

// 区域特定配置
const regionConfigs: { [key: string]: Partial<GlobalizationConfig> } = {
  americas: {
    locale: 'en-US',
    language: 'en',
    country: 'US',
    currency: 'USD',
    timezone: 'America/New_York',
    rtl: false,
  },
  europe: {
    locale: 'en-GB',
    language: 'en',
    country: 'GB',
    currency: 'EUR',
    timezone: 'Europe/London',
    rtl: false,
  },
  asia_pacific: {
    locale: 'en-US',
    language: 'en',
    country: 'SG',
    currency: 'USD',
    timezone: 'Asia/Singapore',
    rtl: false,
  },
};

// 合规配置
const regionComplianceConfigs: { [key: string]: ComplianceSettings } = {
  americas: {
    gdprRequired: false,
    cookieConsentRequired: true,
    dataRetentionDays: 2555, // 7年
    privacyPolicyUrl: '/privacy',
  },
  europe: {
    gdprRequired: true,
    cookieConsentRequired: true,
    dataRetentionDays: 365,
    privacyPolicyUrl: '/privacy',
  },
  asia_pacific: {
    gdprRequired: false,
    cookieConsentRequired: false,
    dataRetentionDays: 1095, // 3年
    privacyPolicyUrl: '/privacy',
  },
};

// 功能开关配置
const regionFeatures: { [key: string]: { [key: string]: boolean } } = {
  americas: {
    advanced_analytics: true,
    social_login: true,
    data_export: true,
    ai_summary: true,
    payment_processing: true,
  },
  europe: {
    advanced_analytics: false, // GDPR限制
    social_login: false,
    data_export: true,
    ai_summary: true,
    payment_processing: true,
  },
  asia_pacific: {
    advanced_analytics: true,
    social_login: true,
    data_export: false,
    ai_summary: true,
    payment_processing: true,
  },
};

// Provider组件
interface GlobalizationProviderProps {
  children: ReactNode;
  initialRegion?: string;
}

export function GlobalizationProvider({ children, initialRegion }: GlobalizationProviderProps) {
  const [config, setConfig] = useState<GlobalizationConfig>(defaultConfig);
  const [metrics, setMetrics] = useState<PerformanceMetrics>(defaultMetrics);
  const [compliance, setCompliance] = useState<ComplianceSettings>(defaultCompliance);
  const router = useRouter();
  const pathname = usePathname();

  // 初始化配置
  useEffect(() => {
    const initializeGlobalization = async () => {
      try {
        // 检测用户区域
        const detectedRegion = initialRegion || await detectUserRegion();
        
        // 应用区域配置
        const regionConfig = regionConfigs[detectedRegion] || regionConfigs.global;
        const newConfig = { ...defaultConfig, region: detectedRegion, ...regionConfig };
        
        // 应用合规配置
        const complianceConfig = regionComplianceConfigs[detectedRegion] || defaultCompliance;
        
        setConfig(newConfig);
        setCompliance(complianceConfig);

        // 获取性能指标
        const performanceMetrics = await fetchPerformanceMetrics(detectedRegion);
        setMetrics(performanceMetrics);

        // 设置HTML属性
        document.documentElement.lang = newConfig.language;
        document.documentElement.dir = newConfig.rtl ? 'rtl' : 'ltr';

        // 存储到localStorage
        localStorage.setItem('attentionsync_region', detectedRegion);
        localStorage.setItem('attentionsync_config', JSON.stringify(newConfig));

      } catch (error) {
        console.error('Failed to initialize globalization:', error);
      }
    };

    initializeGlobalization();
  }, [initialRegion]);

  // 获取性能指标
  const fetchPerformanceMetrics = async (region: string): Promise<PerformanceMetrics> => {
    try {
      const startTime = performance.now();
      const response = await fetch('/api/metrics', {
        headers: {
          'X-Region': region,
        },
      });
      const endTime = performance.now();
      
      const data = await response.json();
      
      return {
        responseTime: endTime - startTime,
        cacheHitRate: data.cache_hit_rate || 0,
        region: region,
        cdnStatus: response.headers.get('X-Cache') || 'unknown',
      };
    } catch (error) {
      console.warn('Failed to fetch performance metrics:', error);
      return defaultMetrics;
    }
  };

  // 更新配置
  const updateConfig = (updates: Partial<GlobalizationConfig>) => {
    const newConfig = { ...config, ...updates };
    setConfig(newConfig);
    
    // 更新HTML属性
    if (updates.language) {
      document.documentElement.lang = updates.language;
    }
    if (updates.rtl !== undefined) {
      document.documentElement.dir = updates.rtl ? 'rtl' : 'ltr';
    }

    // 存储更新
    localStorage.setItem('attentionsync_config', JSON.stringify(newConfig));
  };

  // 格式化货币
  const formatCurrency = (amount: number): string => {
    try {
      return new Intl.NumberFormat(config.locale, {
        style: 'currency',
        currency: config.currency,
      }).format(amount);
    } catch (error) {
      return `${config.currency} ${amount.toFixed(2)}`;
    }
  };

  // 格式化日期
  const formatDate = (date: Date): string => {
    try {
      return new Intl.DateTimeFormat(config.locale, {
        timeZone: config.timezone,
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }).format(date);
    } catch (error) {
      return date.toLocaleDateString();
    }
  };

  // 格式化数字
  const formatNumber = (number: number): string => {
    try {
      return new Intl.NumberFormat(config.locale).format(number);
    } catch (error) {
      return number.toString();
    }
  };

  // 检查功能是否启用
  const isFeatureEnabled = (feature: string): boolean => {
    const features = regionFeatures[config.region] || {};
    return features[feature] ?? true;
  };

  const contextValue: GlobalizationContextType = {
    config,
    metrics,
    compliance,
    updateConfig,
    formatCurrency,
    formatDate,
    formatNumber,
    detectUserRegion,
    isFeatureEnabled,
  };

  return (
    <GlobalizationContext.Provider value={contextValue}>
      {children}
    </GlobalizationContext.Provider>
  );
}

// Hook for using globalization context
export function useGlobalization() {
  const context = useContext(GlobalizationContext);
  if (context === undefined) {
    throw new Error('useGlobalization must be used within a GlobalizationProvider');
  }
  return context;
}

// Region selector component
export function RegionSelector() {
  const { config, updateConfig } = useGlobalization();
  const [isOpen, setIsOpen] = useState(false);

  const regions = [
    { value: 'americas', label: '🌎 Americas', currency: 'USD' },
    { value: 'europe', label: '🌍 Europe', currency: 'EUR' },
    { value: 'asia_pacific', label: '🌏 Asia Pacific', currency: 'USD' },
  ];

  const handleRegionChange = (regionValue: string) => {
    const regionConfig = regionConfigs[regionValue];
    if (regionConfig) {
      updateConfig({ ...regionConfig, region: regionValue });
    }
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        <span>
          {regions.find(r => r.value === config.region)?.label || '🌐 Global'}
        </span>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 z-10 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5">
          <div className="py-1">
            {regions.map((region) => (
              <button
                key={region.value}
                onClick={() => handleRegionChange(region.value)}
                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              >
                <span className="flex-1 text-left">{region.label}</span>
                <span className="text-xs text-gray-500">{region.currency}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Performance indicator component
export function PerformanceIndicator() {
  const { metrics, config } = useGlobalization();
  
  const getStatusColor = (responseTime: number) => {
    if (responseTime < 200) return 'text-green-500';
    if (responseTime < 500) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="flex items-center space-x-2 text-xs text-gray-500">
      <div className="flex items-center space-x-1">
        <div className={`w-2 h-2 rounded-full ${getStatusColor(metrics.responseTime)}`}></div>
        <span>{Math.round(metrics.responseTime)}ms</span>
      </div>
      <span>•</span>
      <span>Cache: {Math.round(metrics.cacheHitRate * 100)}%</span>
      <span>•</span>
      <span>{config.region.toUpperCase()}</span>
    </div>
  );
}

// Compliance banner component
export function ComplianceBanner() {
  const { compliance } = useGlobalization();
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const hasConsented = localStorage.getItem('attentionsync_consent');
    if (compliance.cookieConsentRequired && !hasConsented) {
      setShowBanner(true);
    }
  }, [compliance]);

  const handleAccept = () => {
    localStorage.setItem('attentionsync_consent', 'true');
    setShowBanner(false);
  };

  if (!showBanner) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gray-900 text-white p-4 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm">
            We use cookies to improve your experience and analyze site usage. 
            {compliance.gdprRequired && (
              <span> Your data is processed according to GDPR requirements.</span>
            )}
            <a href={compliance.privacyPolicyUrl} className="underline ml-1">
              Learn more
            </a>
          </p>
        </div>
        <div className="flex space-x-3 ml-4">
          <button
            onClick={() => setShowBanner(false)}
            className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white"
          >
            Decline
          </button>
          <button
            onClick={handleAccept}
            className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Accept
          </button>
        </div>
      </div>
    </div>
  );
}