/**
 * TypeScript type definitions for AttentionSync
 */

export interface User {
  id: number;
  email: string;
  username?: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  is_active: boolean;
  is_verified: boolean;
  is_premium: boolean;
  created_at: string;
  last_login_at?: string;
}

export interface Source {
  id: number;
  name: string;
  description?: string;
  url: string;
  source_type: 'rss' | 'api' | 'webpage' | 'video' | 'podcast' | 'social' | 'email' | 'webhook';
  status: 'active' | 'paused' | 'error' | 'disabled';
  user_id: number;
  total_items: number;
  success_count: number;
  error_count: number;
  created_at: string;
  updated_at: string;
  last_fetched_at?: string;
  last_success_at?: string;
  last_error_at?: string;
  last_error_message?: string;
  config: Record<string, any>;
  headers: Record<string, string>;
  fetch_interval_minutes: number;
}

export interface ItemSummary {
  id: number;
  title: string;
  summary?: string;
  url: string;
  author?: string;
  published_at?: string;
  importance_score: number;
  topics: string[];
  source_name: string;
}

export interface Item extends ItemSummary {
  content?: string;
  source_id: number;
  topics_detailed: Array<{
    name: string;
    confidence: number;
  }>;
  entities: Array<{
    name: string;
    type: string;
    confidence: number;
  }>;
  sentiment_score?: number;
  is_processed: boolean;
  is_duplicate: boolean;
  duplicate_of_id?: number;
  has_video: boolean;
  has_audio: boolean;
  has_images: boolean;
  media_urls: string[];
  view_count: number;
  click_count: number;
  share_count: number;
  created_at: string;
  updated_at: string;
}

export interface Collection {
  id: number;
  name: string;
  description?: string;
  item_count: number;
  is_default: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  username?: string;
  full_name?: string;
}

export interface SourceCreate {
  name: string;
  description?: string;
  url: string;
  source_type: Source['source_type'];
  fetch_interval_minutes?: number;
  config?: Record<string, any>;
  headers?: Record<string, string>;
}

export interface SearchParams {
  q: string;
  limit?: number;
  skip?: number;
  source_id?: number;
}

export interface ApiResponse<T> {
  data?: T;
  error?: {
    type: string;
    message: string;
    details: Record<string, any>;
  };
}

export interface DailyStats {
  date: string;
  total_items: number;
  processed_items: number;
  high_importance_items: number;
  media_items: number;
  processing_rate: number;
}

export interface TrendingTopic {
  topic: string;
  count: number;
}

export interface SourceRecommendation {
  name: string;
  url: string;
  type: string;
  description: string;
}