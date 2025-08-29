-- AttentionSync Database Schema
-- PostgreSQL 15+ Required
-- Created: 2024

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search
CREATE EXTENSION IF NOT EXISTS "vector";   -- For embeddings

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    language VARCHAR(10) DEFAULT 'zh-CN',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    daily_reading_time INTEGER DEFAULT 3, -- minutes
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Sources table (RSS feeds, APIs, etc.)
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'rss', 'api', 'webhook', 'manual'
    platform VARCHAR(50), -- 'wechat', 'bilibili', 'youtube', 'x', 'weibo', etc.
    url TEXT,
    config JSONB DEFAULT '{}', -- API keys, parameters, etc.
    is_active BOOLEAN DEFAULT true,
    last_fetched_at TIMESTAMP WITH TIME ZONE,
    fetch_frequency INTEGER DEFAULT 3600, -- seconds
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, url)
);

-- Create indexes for sources
CREATE INDEX idx_sources_user_id ON sources(user_id);
CREATE INDEX idx_sources_type ON sources(type);
CREATE INDEX idx_sources_platform ON sources(platform);
CREATE INDEX idx_sources_is_active ON sources(is_active);
CREATE INDEX idx_sources_last_fetched ON sources(last_fetched_at);

-- Items table (raw content items)
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
    external_id VARCHAR(500), -- Original ID from source
    url TEXT,
    title TEXT NOT NULL,
    author VARCHAR(255),
    content_type VARCHAR(50) NOT NULL, -- 'article', 'video', 'audio', 'image'
    raw_content TEXT, -- Original HTML/text
    media_url TEXT, -- Video/audio/image URL
    published_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}', -- Platform-specific data
    hash VARCHAR(64), -- For deduplication
    is_processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, external_id)
);

-- Create indexes for items
CREATE INDEX idx_items_source_id ON items(source_id);
CREATE INDEX idx_items_published_at ON items(published_at DESC);
CREATE INDEX idx_items_content_type ON items(content_type);
CREATE INDEX idx_items_hash ON items(hash);
CREATE INDEX idx_items_is_processed ON items(is_processed);
CREATE INDEX idx_items_created_at ON items(created_at DESC);

-- Transcripts table (for audio/video content)
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    language VARCHAR(10),
    text TEXT NOT NULL,
    segments JSONB, -- Timestamped segments
    model VARCHAR(50), -- 'whisper', 'funasr', etc.
    confidence FLOAT,
    duration INTEGER, -- seconds
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for transcripts
CREATE INDEX idx_transcripts_item_id ON transcripts(item_id);
CREATE INDEX idx_transcripts_language ON transcripts(language);

-- Summaries table
CREATE TABLE summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500),
    summary TEXT NOT NULL,
    key_points JSONB, -- Array of key points
    entities JSONB, -- Extracted entities
    tags TEXT[], -- Array of tags
    language VARCHAR(10),
    model VARCHAR(50), -- 'claude-3-sonnet', 'gpt-4', etc.
    tokens_used INTEGER,
    processing_time FLOAT, -- seconds
    quality_score FLOAT, -- 0-1
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_id, user_id)
);

-- Create indexes for summaries
CREATE INDEX idx_summaries_item_id ON summaries(item_id);
CREATE INDEX idx_summaries_user_id ON summaries(user_id);
CREATE INDEX idx_summaries_tags ON summaries USING GIN(tags);
CREATE INDEX idx_summaries_created_at ON summaries(created_at DESC);

-- Embeddings table (for semantic search)
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    summary_id UUID REFERENCES summaries(id) ON DELETE CASCADE,
    embedding vector(1536), -- OpenAI embedding dimension
    model VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for embeddings
CREATE INDEX idx_embeddings_item_id ON embeddings(item_id);
CREATE INDEX idx_embeddings_summary_id ON embeddings(summary_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);

-- Clusters table (topic clustering)
CREATE TABLE clusters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    description TEXT,
    keywords TEXT[],
    date DATE NOT NULL,
    item_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for clusters
CREATE INDEX idx_clusters_user_id ON clusters(user_id);
CREATE INDEX idx_clusters_date ON clusters(date DESC);

-- Cluster items relationship
CREATE TABLE cluster_items (
    cluster_id UUID REFERENCES clusters(id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    similarity_score FLOAT,
    PRIMARY KEY (cluster_id, item_id)
);

-- Preferences table (user preferences and settings)
CREATE TABLE preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    keywords TEXT[], -- Interested keywords
    blocked_keywords TEXT[], -- Filtered keywords
    preferred_sources UUID[], -- Preferred source IDs
    blocked_sources UUID[], -- Blocked source IDs
    reading_time_slots JSONB, -- Preferred reading times
    notification_settings JSONB DEFAULT '{}',
    personalization_enabled BOOLEAN DEFAULT true,
    auto_archive_days INTEGER DEFAULT 30,
    theme VARCHAR(20) DEFAULT 'light',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for preferences
CREATE INDEX idx_preferences_user_id ON preferences(user_id);

-- Interactions table (user behavior tracking)
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'view', 'click', 'save', 'share', 'hide', 'report'
    duration INTEGER, -- Reading time in seconds
    context JSONB DEFAULT '{}', -- Additional context
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for interactions
CREATE INDEX idx_interactions_user_id ON interactions(user_id);
CREATE INDEX idx_interactions_item_id ON interactions(item_id);
CREATE INDEX idx_interactions_action ON interactions(action);
CREATE INDEX idx_interactions_created_at ON interactions(created_at DESC);
CREATE INDEX idx_interactions_user_item ON interactions(user_id, item_id);

-- Daily digests table
CREATE TABLE daily_digests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    items JSONB NOT NULL, -- Array of item IDs with scores
    total_items INTEGER,
    read_items INTEGER DEFAULT 0,
    reading_time INTEGER DEFAULT 0, -- seconds
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, date)
);

-- Create indexes for daily digests
CREATE INDEX idx_daily_digests_user_id ON daily_digests(user_id);
CREATE INDEX idx_daily_digests_date ON daily_digests(date DESC);
CREATE INDEX idx_daily_digests_user_date ON daily_digests(user_id, date DESC);

-- Collections table (user collections/bookmarks)
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    item_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for collections
CREATE INDEX idx_collections_user_id ON collections(user_id);
CREATE INDEX idx_collections_is_public ON collections(is_public);

-- Collection items relationship
CREATE TABLE collection_items (
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    note TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, item_id)
);

-- API keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    permissions JSONB DEFAULT '{}',
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for API keys
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- Audit logs table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit logs
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Create update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clusters_updated_at BEFORE UPDATE ON clusters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collections_updated_at BEFORE UPDATE ON collections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW v_user_daily_stats AS
SELECT 
    u.id as user_id,
    u.username,
    DATE(i.created_at) as date,
    COUNT(DISTINCT i.id) as items_read,
    SUM(CASE WHEN inter.action = 'save' THEN 1 ELSE 0 END) as items_saved,
    SUM(CASE WHEN inter.action = 'share' THEN 1 ELSE 0 END) as items_shared,
    AVG(inter.duration) as avg_reading_time
FROM users u
LEFT JOIN interactions inter ON u.id = inter.user_id
LEFT JOIN items i ON inter.item_id = i.id
GROUP BY u.id, u.username, DATE(i.created_at);

-- Create materialized view for performance
CREATE MATERIALIZED VIEW mv_popular_items AS
SELECT 
    i.id,
    i.title,
    i.published_at,
    COUNT(DISTINCT inter.user_id) as view_count,
    SUM(CASE WHEN inter.action = 'save' THEN 1 ELSE 0 END) as save_count,
    AVG(inter.duration) as avg_reading_time
FROM items i
LEFT JOIN interactions inter ON i.id = inter.item_id
WHERE i.published_at > CURRENT_DATE - INTERVAL '7 days'
GROUP BY i.id, i.title, i.published_at
ORDER BY view_count DESC;

-- Create index on materialized view
CREATE INDEX idx_mv_popular_items_published ON mv_popular_items(published_at DESC);

-- Add comments for documentation
COMMENT ON TABLE users IS '用户基础信息表';
COMMENT ON TABLE sources IS '信息源配置表';
COMMENT ON TABLE items IS '原始内容项表';
COMMENT ON TABLE transcripts IS '音视频转写文本表';
COMMENT ON TABLE summaries IS 'AI生成摘要表';
COMMENT ON TABLE embeddings IS '向量嵌入表（用于语义搜索）';
COMMENT ON TABLE clusters IS '主题聚类表';
COMMENT ON TABLE preferences IS '用户偏好设置表';
COMMENT ON TABLE interactions IS '用户行为交互记录表';
COMMENT ON TABLE daily_digests IS '每日摘要表';
COMMENT ON TABLE collections IS '用户收藏夹表';
COMMENT ON TABLE api_keys IS 'API密钥管理表';
COMMENT ON TABLE audit_logs IS '审计日志表';