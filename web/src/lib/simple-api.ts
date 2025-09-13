/**
 * 简化的 API 客户端
 * 用于测试和调试前端数据流问题
 */

const API_BASE_URL = 'http://localhost:8050/api/v1';

export interface SimpleItem {
  id: number;
  title: string;
  summary: string;
  url: string;
  source: string;
  published_at: string;
  read_time: number;
  category: string;
}

export interface DailyDigestResponse {
  items: SimpleItem[];
  total: number;
  generated_at: string;
  estimated_read_time: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  service: string;
}

class SimpleAPIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    console.log(`[SimpleAPI] Making request to: ${url}`);
    
    const defaultOptions: RequestInit = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      console.log(`[SimpleAPI] Response status: ${response.status}`);
      console.log(`[SimpleAPI] Response headers:`, Object.fromEntries(response.headers.entries()));
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log(`[SimpleAPI] Response data:`, data);
      
      return data;
    } catch (error) {
      console.error(`[SimpleAPI] Request failed:`, error);
      throw error;
    }
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async getDailyDigest(): Promise<DailyDigestResponse> {
    return this.request<DailyDigestResponse>('/daily/digest');
  }

  async getSources(): Promise<any> {
    return this.request('/sources');
  }

  // 测试连接
  async testConnection(): Promise<boolean> {
    try {
      const health = await this.getHealth();
      console.log('[SimpleAPI] Connection test successful:', health);
      return health.status === 'ok';
    } catch (error) {
      console.error('[SimpleAPI] Connection test failed:', error);
      return false;
    }
  }
}

// 创建全局实例
export const simpleAPI = new SimpleAPIClient();

// 导出类型
export type { SimpleItem, DailyDigestResponse, HealthResponse };