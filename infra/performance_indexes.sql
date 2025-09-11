-- AttentionSync 性能优化索引
-- 基于实际使用场景的额外索引优化

-- 复合索引优化（基于常见查询模式）

-- 用户每日摘要查询优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_daily_digests_user_date_accessed 
ON daily_digests(user_id, date DESC, accessed_at);

-- 用户活跃源查询优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sources_user_active_fetch 
ON sources(user_id, is_active, last_fetched_at DESC) 
WHERE is_active = true;

-- 待处理内容查询优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_items_unprocessed_published 
ON items(is_processed, published_at DESC) 
WHERE is_processed = false;

-- 用户交互分析优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interactions_user_action_created 
ON interactions(user_id, action, created_at DESC);

-- 内容去重查询优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_items_hash_published 
ON items(hash, published_at DESC) 
WHERE hash IS NOT NULL;

-- 摘要质量分析优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_summaries_model_quality_created 
ON summaries(model, quality_score DESC, created_at DESC);

-- 用户偏好匹配优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_preferences_personalization 
ON preferences(user_id, personalization_enabled) 
WHERE personalization_enabled = true;

-- 集合项目查询优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_collection_items_collection_added 
ON collection_items(collection_id, added_at DESC);

-- API 密钥查询优化
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_hash_active_expires 
ON api_keys(key_hash, is_active, expires_at) 
WHERE is_active = true;

-- 分区表优化建议（对于大数据量场景）
-- 按月分区 interactions 表
-- CREATE TABLE interactions_y2024m01 PARTITION OF interactions
-- FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- 统计信息更新
-- 定期更新表统计信息以优化查询计划
-- ANALYZE users;
-- ANALYZE sources;
-- ANALYZE items;
-- ANALYZE interactions;
-- ANALYZE summaries;

-- 查询性能监控视图
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 20;

-- 表大小监控视图
CREATE OR REPLACE VIEW v_table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- 索引使用情况监控
CREATE OR REPLACE VIEW v_index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 数据库连接监控
CREATE OR REPLACE VIEW v_connection_stats AS
SELECT 
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched,
    tup_inserted,
    tup_updated,
    tup_deleted
FROM pg_stat_database 
WHERE datname = current_database();

-- 性能优化建议注释
COMMENT ON VIEW v_slow_queries IS '慢查询监控视图 - 用于识别需要优化的查询';
COMMENT ON VIEW v_table_sizes IS '表大小监控视图 - 用于容量规划';
COMMENT ON VIEW v_index_usage IS '索引使用情况监控 - 用于识别无用索引';
COMMENT ON VIEW v_connection_stats IS '数据库连接统计 - 用于性能监控';

-- 自动化维护任务建议
-- 1. 定期 VACUUM 和 ANALYZE
-- 2. 重建碎片化严重的索引
-- 3. 清理过期的审计日志和交互记录
-- 4. 更新物化视图