'use client';

import { useState, useEffect } from 'react';
import { simpleAPI, type DailyDigestResponse, type HealthResponse } from '@/lib/simple-api';

export function SimpleTest() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [digest, setDigest] = useState<DailyDigestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'failed'>('checking');

  // 测试API连接
  const testConnection = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const isConnected = await simpleAPI.testConnection();
      setConnectionStatus(isConnected ? 'connected' : 'failed');
      
      if (isConnected) {
        const healthData = await simpleAPI.getHealth();
        setHealth(healthData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setConnectionStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  // 测试每日摘要
  const testDailyDigest = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const digestData = await simpleAPI.getDailyDigest();
      setDigest(digestData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // 页面加载时自动测试连接
  useEffect(() => {
    testConnection();
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6">🧪 AttentionSync 数据流测试</h2>
      
      {/* 连接状态 */}
      <div className="mb-6 p-4 rounded-lg border">
        <h3 className="text-lg font-semibold mb-2">API 连接状态</h3>
        <div className="flex items-center gap-4">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            connectionStatus === 'connected' ? 'bg-green-100 text-green-800' :
            connectionStatus === 'failed' ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {connectionStatus === 'connected' ? '✅ 已连接' :
             connectionStatus === 'failed' ? '❌ 连接失败' :
             '🔄 检查中...'}
          </div>
          <button
            onClick={testConnection}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? '测试中...' : '重新测试'}
          </button>
        </div>
        
        {health && (
          <div className="mt-3 text-sm text-gray-600">
            <p><strong>服务:</strong> {health.service}</p>
            <p><strong>版本:</strong> {health.version}</p>
            <p><strong>时间:</strong> {new Date(health.timestamp).toLocaleString()}</p>
          </div>
        )}
      </div>

      {/* 每日摘要测试 */}
      <div className="mb-6 p-4 rounded-lg border">
        <h3 className="text-lg font-semibold mb-2">每日摘要测试</h3>
        <button
          onClick={testDailyDigest}
          disabled={loading || connectionStatus !== 'connected'}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
        >
          {loading ? '加载中...' : '测试每日摘要'}
        </button>
        
        {digest && (
          <div className="mt-4">
            <div className="text-sm text-gray-600 mb-3">
              <p><strong>总项目数:</strong> {digest.total}</p>
              <p><strong>预计阅读时间:</strong> {digest.estimated_read_time} 分钟</p>
              <p><strong>生成时间:</strong> {new Date(digest.generated_at).toLocaleString()}</p>
            </div>
            
            <div className="space-y-3">
              {digest.items.map((item) => (
                <div key={item.id} className="p-3 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900">{item.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{item.summary}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>来源: {item.source}</span>
                    <span>分类: {item.category}</span>
                    <span>阅读时间: {item.read_time}分钟</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 错误显示 */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <h4 className="text-red-800 font-medium">错误信息</h4>
          <p className="text-red-600 text-sm mt-1">{error}</p>
        </div>
      )}

      {/* 调试信息 */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-2">调试信息</h3>
        <div className="text-sm text-gray-600 space-y-1">
          <p><strong>API 基础URL:</strong> http://localhost:8050/api/v1</p>
          <p><strong>当前时间:</strong> {new Date().toLocaleString()}</p>
          <p><strong>用户代理:</strong> {navigator.userAgent}</p>
        </div>
      </div>
    </div>
  );
}