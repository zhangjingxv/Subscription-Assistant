import { api } from './api-client-optimized';
import type { LoginCredentials } from '@/types';

export const apiClient = {
  async login(credentials: LoginCredentials) {
    const res = await api.login(credentials.email, credentials.password);
    try {
      if (typeof window !== 'undefined') {
        if ((res as any)?.access_token) {
          localStorage.setItem('access_token', (res as any).access_token);
        }
        if ((res as any)?.refresh_token) {
          localStorage.setItem('refresh_token', (res as any).refresh_token);
        }
        if ((res as any)?.user) {
          localStorage.setItem('user', JSON.stringify((res as any).user));
        }
      }
    } catch {}
    return res;
  },
  async getDailyDigest(params?: any) {
    try {
      const res = await api.getDailyDigest(params);
      console.log('API Response:', res);
      // 转换API响应格式以匹配前端期望的格式
      if (res && res.items) {
        const transformedItems = res.items.map((item: any) => ({
          id: item.id,
          title: item.title,
          summary: item.content,
          url: item.url,
          author: item.source,
          published_at: item.published_at,
          importance_score: 0.8,
          topics: [],
          source_name: item.source
        }));
        console.log('Transformed items:', transformedItems);
        return transformedItems;
      }
      console.log('No items found in response');
      return [];
    } catch (error) {
      console.error('Error in getDailyDigest:', error);
      throw error;
    }
  },
  async recordDigestFeedback(itemId: string | number, action: string) {
    return api.recordDigestFeedback(String(itemId), action);
  },
  async recordShare(itemId: string | number) {
    return api.recordShare(String(itemId));
  },
};

export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('access_token');
}

export function getStoredUser(): any | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

