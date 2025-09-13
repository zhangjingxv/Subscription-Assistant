'use client';

import { useEffect, useState, useRef } from 'react';

interface PerformanceMetrics {
  fcp: number | null; // First Contentful Paint
  lcp: number | null; // Largest Contentful Paint
  fid: number | null; // First Input Delay
  cls: number | null; // Cumulative Layout Shift
  ttfb: number | null; // Time to First Byte
  domContentLoaded: number | null;
  loadComplete: number | null;
  memoryUsage: number | null;
}

interface PerformanceMonitorProps {
  enabled?: boolean;
  onMetricsUpdate?: (metrics: PerformanceMetrics) => void;
  showInConsole?: boolean;
}

export function PerformanceMonitor({ 
  enabled = true, 
  onMetricsUpdate,
  showInConsole = false 
}: PerformanceMonitorProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fcp: null,
    lcp: null,
    fid: null,
    cls: null,
    ttfb: null,
    domContentLoaded: null,
    loadComplete: null,
    memoryUsage: null
  });

  const observerRef = useRef<PerformanceObserver | null>(null);

  useEffect(() => {
    if (!enabled || typeof window === 'undefined') return;

    const updateMetrics = (newMetrics: Partial<PerformanceMetrics>) => {
      setMetrics(prev => {
        const updated = { ...prev, ...newMetrics };
        onMetricsUpdate?.(updated);
        
        if (showInConsole) {
          console.log('Performance Metrics:', updated);
        }
        
        return updated;
      });
    };

    // 获取基本性能指标
    const getBasicMetrics = () => {
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      
      if (navigation) {
        updateMetrics({
          ttfb: navigation.responseStart - navigation.requestStart,
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.navigationStart,
          loadComplete: navigation.loadEventEnd - navigation.navigationStart
        });
      }

      // 获取内存使用情况（如果支持）
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        updateMetrics({
          memoryUsage: memory.usedJSHeapSize / 1024 / 1024 // MB
        });
      }
    };

    // 设置 Performance Observer
    const setupObservers = () => {
      // FCP (First Contentful Paint)
      if ('PerformanceObserver' in window) {
        try {
          observerRef.current = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (entry.name === 'first-contentful-paint') {
                updateMetrics({ fcp: entry.startTime });
              }
            }
          });
          observerRef.current.observe({ entryTypes: ['paint'] });
        } catch (error) {
          console.warn('Failed to observe paint entries:', error);
        }

        // LCP (Largest Contentful Paint)
        try {
          const lcpObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            updateMetrics({ lcp: lastEntry.startTime });
          });
          lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        } catch (error) {
          console.warn('Failed to observe LCP:', error);
        }

        // FID (First Input Delay)
        try {
          const fidObserver = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              const fidEntry = entry as any;
              updateMetrics({ fid: fidEntry.processingStart - fidEntry.startTime });
            }
          });
          fidObserver.observe({ entryTypes: ['first-input'] });
        } catch (error) {
          console.warn('Failed to observe FID:', error);
        }

        // CLS (Cumulative Layout Shift)
        try {
          let clsValue = 0;
          const clsObserver = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              const clsEntry = entry as any;
              if (!clsEntry.hadRecentInput) {
                clsValue += clsEntry.value;
                updateMetrics({ cls: clsValue });
              }
            }
          });
          clsObserver.observe({ entryTypes: ['layout-shift'] });
        } catch (error) {
          console.warn('Failed to observe CLS:', error);
        }
      }
    };

    // 页面加载完成后获取指标
    const handleLoad = () => {
      getBasicMetrics();
      setupObservers();
    };

    if (document.readyState === 'complete') {
      handleLoad();
    } else {
      window.addEventListener('load', handleLoad);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
      window.removeEventListener('load', handleLoad);
    };
  }, [enabled, onMetricsUpdate, showInConsole]);

  // 性能评分计算
  const getPerformanceScore = (): number => {
    let score = 100;
    
    // FCP 评分 (0-3秒为优秀)
    if (metrics.fcp !== null) {
      if (metrics.fcp > 3000) score -= 20;
      else if (metrics.fcp > 2000) score -= 10;
    }
    
    // LCP 评分 (0-2.5秒为优秀)
    if (metrics.lcp !== null) {
      if (metrics.lcp > 4000) score -= 20;
      else if (metrics.lcp > 2500) score -= 10;
    }
    
    // FID 评分 (0-100ms为优秀)
    if (metrics.fid !== null) {
      if (metrics.fid > 300) score -= 20;
      else if (metrics.fid > 100) score -= 10;
    }
    
    // CLS 评分 (0-0.1为优秀)
    if (metrics.cls !== null) {
      if (metrics.cls > 0.25) score -= 20;
      else if (metrics.cls > 0.1) score -= 10;
    }
    
    return Math.max(0, score);
  };

  const score = getPerformanceScore();
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return '优秀';
    if (score >= 70) return '良好';
    if (score >= 50) return '一般';
    return '需要优化';
  };

  return (
    <div className="fixed bottom-4 left-4 bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm">
      <h3 className="text-sm font-semibold text-gray-900 mb-2">性能监控</h3>
      
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-600">性能评分:</span>
          <span className={`font-medium ${getScoreColor(score)}`}>
            {score}/100 ({getScoreLabel(score)})
          </span>
        </div>
        
        {metrics.fcp !== null && (
          <div className="flex justify-between">
            <span className="text-gray-600">FCP:</span>
            <span className="font-mono">{metrics.fcp.toFixed(0)}ms</span>
          </div>
        )}
        
        {metrics.lcp !== null && (
          <div className="flex justify-between">
            <span className="text-gray-600">LCP:</span>
            <span className="font-mono">{metrics.lcp.toFixed(0)}ms</span>
          </div>
        )}
        
        {metrics.fid !== null && (
          <div className="flex justify-between">
            <span className="text-gray-600">FID:</span>
            <span className="font-mono">{metrics.fid.toFixed(0)}ms</span>
          </div>
        )}
        
        {metrics.cls !== null && (
          <div className="flex justify-between">
            <span className="text-gray-600">CLS:</span>
            <span className="font-mono">{metrics.cls.toFixed(3)}</span>
          </div>
        )}
        
        {metrics.ttfb !== null && (
          <div className="flex justify-between">
            <span className="text-gray-600">TTFB:</span>
            <span className="font-mono">{metrics.ttfb.toFixed(0)}ms</span>
          </div>
        )}
        
        {metrics.memoryUsage !== null && (
          <div className="flex justify-between">
            <span className="text-gray-600">内存:</span>
            <span className="font-mono">{metrics.memoryUsage.toFixed(1)}MB</span>
          </div>
        )}
      </div>
    </div>
  );
}

// Hook 用于在组件中获取性能指标
export function usePerformanceMetrics() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fcp: null,
    lcp: null,
    fid: null,
    cls: null,
    ttfb: null,
    domContentLoaded: null,
    loadComplete: null,
    memoryUsage: null
  });

  useEffect(() => {
    const monitor = new PerformanceMonitor({
      enabled: true,
      onMetricsUpdate: setMetrics,
      showInConsole: false
    });

    return () => {
      // 清理逻辑
    };
  }, []);

  return metrics;
}

export default PerformanceMonitor;