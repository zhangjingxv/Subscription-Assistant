/**
 * 优化的 API 客户端
 * 支持请求去重、智能缓存、错误重试等功能
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import toast from 'react-hot-toast';

// 类型定义
interface RequestCacheItem {
  promise: Promise<any>;
  timestamp: number;
}

interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
}

interface APIClientConfig {
  baseURL: string;
  timeout: number;
  cacheTimeout: number;
  retryConfig: RetryConfig;
}

class APIClientOptimized {
  private axiosInstance: AxiosInstance;
  private requestCache = new Map<string, RequestCacheItem>();
  private cacheTimeout: number;
  private retryConfig: RetryConfig;
  private pendingRequests = new Map<string, AbortController>();

  constructor(config: APIClientConfig) {
    this.cacheTimeout = config.cacheTimeout;
    this.retryConfig = config.retryConfig;

    // 创建 axios 实例
    this.axiosInstance = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器
    this.axiosInstance.interceptors.request.use(
      (config) => {
        // 添加认证 token
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // 添加请求 ID
        config.metadata = {
          requestId: this.generateRequestId(),
          startTime: Date.now(),
        };

        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器
    this.axiosInstance.interceptors.response.use(
      (response) => {
        // 记录请求时间
        const start = response.config.metadata?.startTime ?? Date.now();
        const duration = Date.now() - start;
        if (duration > 1000) {
          console.warn(`Slow API request: ${response.config.url} took ${duration}ms`);
        }

        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Token 过期处理
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            await this.refreshToken();
            const token = this.getAuthToken();
            if (token) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return this.axiosInstance(originalRequest);
            }
          } catch (refreshError) {
            // 刷新失败，跳转到登录页
            this.handleAuthError();
            return Promise.reject(refreshError);
          }
        }

        // 网络错误重试
        if (this.shouldRetry(error) && !originalRequest._retryCount) {
          return this.retryRequest(originalRequest, error);
        }

        // 错误处理
        this.handleError(error);
        return Promise.reject(error);
      }
    );
  }

  private generateRequestId(): string {
    return Math.random().toString(36).substring(2, 15);
  }

  private getAuthToken(): string | null {
    return localStorage.getItem('access_token');
  }

  private async refreshToken(): Promise<void> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await axios.post(`${this.axiosInstance.defaults.baseURL}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token: newRefreshToken } = response.data;
      
      localStorage.setItem('access_token', access_token);
      if (newRefreshToken) {
        localStorage.setItem('refresh_token', newRefreshToken);
      }
    } catch (error) {
      // 清理无效 token
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      throw error;
    }
  }

  private handleAuthError() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // 跳转到登录页
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }

  private shouldRetry(error: any): boolean {
    // 网络错误或服务器错误才重试
    return (
      !error.response ||
      error.response.status >= 500 ||
      error.code === 'NETWORK_ERROR' ||
      error.code === 'TIMEOUT'
    );
  }

  private async retryRequest(originalRequest: any, error: any): Promise<any> {
    originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

    if (originalRequest._retryCount > this.retryConfig.maxRetries) {
      return Promise.reject(error);
    }

    // 指数退避延迟
    const delay = Math.min(
      this.retryConfig.baseDelay * Math.pow(2, originalRequest._retryCount - 1),
      this.retryConfig.maxDelay
    );

    await new Promise(resolve => setTimeout(resolve, delay));

    return this.axiosInstance(originalRequest);
  }

  private handleError(error: any) {
    if (error.response) {
      // 服务器响应错误
      const message = error.response.data?.error?.message || '请求失败';
      
      // 根据状态码显示不同的错误信息
      switch (error.response.status) {
        case 400:
          toast.error(`请求参数错误: ${message}`);
          break;
        case 401:
          toast.error('认证失败，请重新登录');
          break;
        case 403:
          toast.error('权限不足');
          break;
        case 404:
          toast.error('请求的资源不存在');
          break;
        case 429:
          toast.error('请求过于频繁，请稍后再试');
          break;
        case 500:
          toast.error('服务器内部错误');
          break;
        default:
          toast.error(message);
      }
    } else if (error.request) {
      // 网络错误
      toast.error('网络连接失败，请检查网络设置');
    } else {
      // 其他错误
      toast.error('发生未知错误');
    }
  }

  private generateCacheKey(method: string, url: string, params?: any): string {
    const paramString = params ? JSON.stringify(params) : '';
    return `${method}:${url}:${paramString}`;
  }

  private async getCachedRequest<T>(cacheKey: string): Promise<T | null> {
    const cached = this.requestCache.get(cacheKey);
    if (!cached) return null;

    // 检查缓存是否过期
    if (Date.now() - cached.timestamp > this.cacheTimeout) {
      this.requestCache.delete(cacheKey);
      return null;
    }

    try {
      return await cached.promise;
    } catch (error) {
      // 缓存的请求失败，删除缓存
      this.requestCache.delete(cacheKey);
      throw error;
    }
  }

  private setCachedRequest(cacheKey: string, promise: Promise<any>) {
    this.requestCache.set(cacheKey, {
      promise,
      timestamp: Date.now(),
    });

    // 请求完成后，根据结果决定是否保留缓存
    promise.catch(() => {
      this.requestCache.delete(cacheKey);
    });
  }

  // 通用请求方法
  async request<T>(config: AxiosRequestConfig & { cache?: boolean }): Promise<T> {
    const { cache = false, ...axiosConfig } = config;
    const method = (axiosConfig.method || 'GET').toUpperCase();
    const url = axiosConfig.url || '';

    // 生成缓存键
    const cacheKey = this.generateCacheKey(method, url, {
      params: axiosConfig.params,
      data: axiosConfig.data,
    });

    // 对于 GET 请求，检查缓存和去重
    if (method === 'GET') {
      // 检查缓存
      if (cache) {
        const cachedResult = await this.getCachedRequest<T>(cacheKey);
        if (cachedResult !== null) {
          return cachedResult;
        }
      }

      // 检查是否有相同的请求正在进行（请求去重）
      if (this.requestCache.has(cacheKey)) {
        return this.requestCache.get(cacheKey)!.promise;
      }
    }

    // 取消之前相同的请求（对于非GET请求）
    if (method !== 'GET') {
      const existingController = this.pendingRequests.get(cacheKey);
      if (existingController) {
        existingController.abort();
      }
    }

    // 创建新的 AbortController
    const abortController = new AbortController();
    axiosConfig.signal = abortController.signal;
    this.pendingRequests.set(cacheKey, abortController);

    // 执行请求
    const promise = this.axiosInstance.request<T>(axiosConfig).then(response => {
      this.pendingRequests.delete(cacheKey);
      return response.data;
    }).catch(error => {
      this.pendingRequests.delete(cacheKey);
      throw error;
    });

    // 缓存 GET 请求
    if (method === 'GET' && cache) {
      this.setCachedRequest(cacheKey, promise);
    }

    return promise;
  }

  // 便捷方法
  async get<T>(url: string, params?: any, cache = true): Promise<T> {
    return this.request<T>({
      method: 'GET',
      url,
      params,
      cache,
    });
  }

  async post<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({
      method: 'POST',
      url,
      data,
    });
  }

  async put<T>(url: string, data?: any): Promise<T> {
    return this.request<T>({
      method: 'PUT',
      url,
      data,
    });
  }

  async delete<T>(url: string): Promise<T> {
    return this.request<T>({
      method: 'DELETE',
      url,
    });
  }

  // 批量请求
  async batchRequest<T>(requests: AxiosRequestConfig[]): Promise<T[]> {
    const promises = requests.map(config => this.request<T>(config));
    return Promise.all(promises);
  }

  // 清理缓存
  clearCache() {
    this.requestCache.clear();
  }

  // 取消所有待处理的请求
  cancelAllRequests() {
    this.pendingRequests.forEach(controller => {
      controller.abort();
    });
    this.pendingRequests.clear();
  }

  // 获取缓存统计
  getCacheStats() {
    const now = Date.now();
    let validCacheCount = 0;
    let expiredCacheCount = 0;

    this.requestCache.forEach(({ timestamp }) => {
      if (now - timestamp > this.cacheTimeout) {
        expiredCacheCount++;
      } else {
        validCacheCount++;
      }
    });

    return {
      totalCached: this.requestCache.size,
      validCached: validCacheCount,
      expiredCached: expiredCacheCount,
      pendingRequests: this.pendingRequests.size,
    };
  }
}

// 默认配置
const defaultConfig: APIClientConfig = {
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8050/api/v1',
  timeout: 30000, // 30秒
  cacheTimeout: 5 * 60 * 1000, // 5分钟
  retryConfig: {
    maxRetries: 3,
    baseDelay: 1000, // 1秒
    maxDelay: 10000, // 10秒
  },
};

// 创建全局实例
export const apiClient = new APIClientOptimized(defaultConfig);

// 具体的 API 方法
export class AttentionSyncAPI {
  private client: APIClientOptimized;

  constructor(client: APIClientOptimized) {
    this.client = client;
  }

  // 认证相关
  async login(email: string, password: string) {
    return this.client.post('/auth/login', { email, password });
  }

  async register(userData: any) {
    return this.client.post('/auth/register', userData);
  }

  async refreshToken(refreshToken: string) {
    return this.client.post('/auth/refresh', { refresh_token: refreshToken });
  }

  async getCurrentUser() {
    return this.client.get('/auth/me', null, true); // 缓存用户信息
  }

  // 信息源相关
  async getSources() {
    return this.client.get('/sources', null, true);
  }

  async createSource(sourceData: any) {
    return this.client.post('/sources', sourceData);
  }

  async updateSource(sourceId: string, sourceData: any) {
    return this.client.put(`/sources/${sourceId}`, sourceData);
  }

  async deleteSource(sourceId: string) {
    return this.client.delete(`/sources/${sourceId}`);
  }

  // 内容相关
  async getDailyDigest(params?: any) {
    return this.client.get('/daily/digest', params, true);
  }

  async getItems(params?: any) {
    return this.client.get('/items', params, true);
  }

  async recordDigestFeedback(itemId: string, action: string) {
    return this.client.post(`/items/${itemId}/feedback`, { action });
  }

  async recordShare(itemId: string) {
    return this.client.post(`/items/${itemId}/share`);
  }

  // 搜索相关
  async search(query: string, filters?: any) {
    return this.client.get('/search', { q: query, ...filters }, true);
  }

  // 统计相关
  async getStats() {
    return this.client.get('/sources/stats/overview', null, true);
  }
}

// 导出 API 实例
export const api = new AttentionSyncAPI(apiClient);

// 导出类型
export type { APIClientConfig, RetryConfig };

export default apiClient;