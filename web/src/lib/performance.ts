/**
 * 前端性能优化工具
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

// 防抖 Hook
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// 节流 Hook
export function useThrottle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T {
  const lastRun = useRef(Date.now());

  return useCallback(
    ((...args) => {
      if (Date.now() - lastRun.current >= delay) {
        func(...args);
        lastRun.current = Date.now();
      }
    }) as T,
    [func, delay]
  );
}

// 虚拟滚动 Hook
export function useVirtualScroll<T>(
  items: T[],
  itemHeight: number,
  containerHeight: number
) {
  const [scrollTop, setScrollTop] = useState(0);

  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const startIndex = Math.floor(scrollTop / itemHeight);
  const endIndex = Math.min(startIndex + visibleCount + 1, items.length);

  const visibleItems = useMemo(
    () => items.slice(startIndex, endIndex),
    [items, startIndex, endIndex]
  );

  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  return {
    visibleItems,
    totalHeight,
    offsetY,
    setScrollTop,
  };
}

// 图片懒加载 Hook
export function useLazyImage(src: string, placeholder?: string) {
  const [imageSrc, setImageSrc] = useState(placeholder || '');
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          const img = new Image();
          img.onload = () => {
            setImageSrc(src);
            setIsLoaded(true);
          };
          img.onerror = () => {
            setIsError(true);
          };
          img.src = src;
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [src]);

  return { imageSrc, isLoaded, isError, imgRef };
}

// 内存泄漏防护 Hook
export function useAsyncEffect(
  effect: () => Promise<void>,
  deps: React.DependencyList
) {
  useEffect(() => {
    let cancelled = false;

    const runEffect = async () => {
      try {
        await effect();
      } catch (error) {
        if (!cancelled) {
          console.error('Async effect error:', error);
        }
      }
    };

    runEffect();

    return () => {
      cancelled = true;
    };
  }, deps);
}

// 性能监控
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Map<string, number[]> = new Map();

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  // 记录性能指标
  recordMetric(name: string, value: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    this.metrics.get(name)!.push(value);
    
    // 只保留最近100个数据点
    const values = this.metrics.get(name)!;
    if (values.length > 100) {
      values.shift();
    }
  }

  // 获取平均值
  getAverageMetric(name: string): number {
    const values = this.metrics.get(name);
    if (!values || values.length === 0) return 0;
    return values.reduce((sum, val) => sum + val, 0) / values.length;
  }

  // 测量函数执行时间
  measureFunction<T extends (...args: any[]) => any>(
    name: string,
    func: T
  ): T {
    return ((...args: any[]) => {
      const startTime = performance.now();
      const result = func(...args);
      const endTime = performance.now();
      this.recordMetric(name, endTime - startTime);
      return result;
    }) as T;
  }

  // 获取所有指标
  getAllMetrics(): Record<string, number> {
    const result: Record<string, number> = {};
    this.metrics.forEach((values, name) => {
      result[name] = this.getAverageMetric(name);
    });
    return result;
  }
}

// Web Vitals 监控
export function reportWebVitals(metric: any) {
  const monitor = PerformanceMonitor.getInstance();
  monitor.recordMetric(metric.name, metric.value);
  
  // 在开发环境下打印到控制台
  if (process.env.NODE_ENV === 'development') {
    console.log(`${metric.name}: ${metric.value}`);
  }
  
  // 在生产环境下发送到监控服务
  if (process.env.NODE_ENV === 'production') {
    // 这里可以发送到你的监控服务
    // analytics.track('Web Vital', metric);
  }
}

// 缓存管理
export class ClientCache {
  private static instance: ClientCache;
  private cache = new Map<string, { data: any; expiry: number }>();
  private maxSize = 100;

  static getInstance(): ClientCache {
    if (!ClientCache.instance) {
      ClientCache.instance = new ClientCache();
    }
    return ClientCache.instance;
  }

  set(key: string, data: any, ttlMs: number = 5 * 60 * 1000) {
    // 清理过期缓存
    this.cleanup();
    
    // 如果缓存已满，删除最旧的条目
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(key, {
      data,
      expiry: Date.now() + ttlMs,
    });
  }

  get(key: string): any | null {
    const item = this.cache.get(key);
    if (!item) return null;

    if (Date.now() > item.expiry) {
      this.cache.delete(key);
      return null;
    }

    return item.data;
  }

  clear() {
    this.cache.clear();
  }

  private cleanup() {
    const now = Date.now();
    const keysToDelete: string[] = [];
    this.cache.forEach((item, key) => {
      if (now > item.expiry) {
        keysToDelete.push(key);
      }
    });
    keysToDelete.forEach((key) => this.cache.delete(key));
  }
}

// 批量请求工具
export class RequestBatcher {
  private batches = new Map<string, {
    requests: Array<{ resolve: Function; reject: Function; params: any }>;
    timeout: NodeJS.Timeout;
  }>();

  batch<T>(
    key: string,
    params: any,
    fetcher: (batchParams: any[]) => Promise<T[]>,
    delay: number = 10
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      if (!this.batches.has(key)) {
        this.batches.set(key, {
          requests: [],
          timeout: setTimeout(() => this.executeBatch(key, fetcher), delay),
        });
      }

      const batch = this.batches.get(key)!;
      batch.requests.push({ resolve, reject, params });
    });
  }

  private async executeBatch<T>(
    key: string,
    fetcher: (batchParams: any[]) => Promise<T[]>
  ) {
    const batch = this.batches.get(key);
    if (!batch) return;

    this.batches.delete(key);

    try {
      const allParams = batch.requests.map(req => req.params);
      const results = await fetcher(allParams);
      
      batch.requests.forEach((req, index) => {
        req.resolve(results[index]);
      });
    } catch (error) {
      batch.requests.forEach(req => {
        req.reject(error);
      });
    }
  }
}

export const requestBatcher = new RequestBatcher();