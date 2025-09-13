#!/usr/bin/env python3
"""
简化的 AttentionSync API 服务 - 修复版
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime
import random

class SimpleAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/health':
            self.handle_health()
        elif path == '/api/v1/health':
            self.handle_health()
        elif path == '/api/v1/daily/digest':
            self.handle_daily_digest()
        elif path == '/api/v1/sources':
            self.handle_sources()
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """发送CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
    
    def handle_health(self):
        """健康检查端点"""
        response = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "service": "AttentionSync API"
        }
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_daily_digest(self):
        """每日摘要端点"""
        sample_items = [
            {
                "id": 1,
                "title": "人工智能在医疗领域的突破性进展",
                "summary": "最新研究显示，AI技术在疾病诊断和治疗方面取得了重大突破，准确率提升至95%以上。",
                "url": "https://example.com/ai-medical-breakthrough",
                "source": "科技日报",
                "published_at": "2024-01-15T10:00:00Z",
                "read_time": 3,
                "category": "科技"
            },
            {
                "id": 2,
                "title": "全球气候变化对经济的影响分析",
                "summary": "专家预测，气候变化将在未来十年内对全球经济造成数万亿美元的损失。",
                "url": "https://example.com/climate-economy-impact",
                "source": "经济观察报",
                "published_at": "2024-01-15T09:30:00Z",
                "read_time": 5,
                "category": "经济"
            },
            {
                "id": 3,
                "title": "新型电池技术突破，充电速度提升10倍",
                "summary": "科学家开发出新型固态电池，充电时间从数小时缩短到几分钟。",
                "url": "https://example.com/battery-breakthrough",
                "source": "科学网",
                "published_at": "2024-01-15T08:15:00Z",
                "read_time": 4,
                "category": "科技"
            }
        ]
        
        selected_items = random.sample(sample_items, random.randint(2, 3))
        
        response = {
            "items": selected_items,
            "total": len(selected_items),
            "generated_at": datetime.now().isoformat(),
            "estimated_read_time": sum(item["read_time"] for item in selected_items)
        }
        
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def handle_sources(self):
        """信息源端点"""
        sources = [
            {
                "id": 1,
                "name": "科技日报",
                "url": "https://example.com/tech-daily",
                "type": "rss",
                "status": "active",
                "last_updated": "2024-01-15T10:00:00Z"
            },
            {
                "id": 2,
                "name": "经济观察报",
                "url": "https://example.com/economy-obs",
                "type": "rss",
                "status": "active",
                "last_updated": "2024-01-15T09:30:00Z"
            }
        ]
        
        response = {
            "sources": sources,
            "total": len(sources)
        }
        
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

def run_server(port=8050):
    """启动服务器"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, SimpleAPIHandler)
    
    print(f"🚀 简化API服务启动在端口 {port}")
    print(f"📡 健康检查: http://localhost:{port}/health")
    print(f"📰 每日摘要: http://localhost:{port}/api/v1/daily/digest")
    print(f"📚 信息源: http://localhost:{port}/api/v1/sources")
    print("按 Ctrl+C 停止服务")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
        httpd.shutdown()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8050
    run_server(port)