#!/usr/bin/env python3
"""
AttentionSync - World Class Edition
"Perfection is achieved when there is nothing left to take away."
"""
import sqlite3
import hashlib
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from xml.etree import ElementTree
from urllib.request import urlopen

# === The Entire System in 150 lines ===

DB = sqlite3.connect(':memory:', check_same_thread=False)
DB.row_factory = sqlite3.Row
DB.executescript("""
    CREATE TABLE items (
        id INTEGER PRIMARY KEY,
        hash TEXT UNIQUE,
        title TEXT,
        url TEXT,
        content TEXT,
        time INTEGER
    );
    CREATE INDEX idx_time ON items(time DESC);
""")

def fetch_rss(url):
    """Fetch RSS - no libraries needed"""
    try:
        xml = urlopen(url, timeout=5).read()
        root = ElementTree.fromstring(xml)
        items = []
        for item in root.findall('.//item')[:10]:
            title = item.findtext('title', '')
            link = item.findtext('link', '')
            desc = item.findtext('description', '')
            items.append({
                'title': title[:100],
                'url': link,
                'content': desc[:500],
                'hash': hashlib.md5(link.encode()).hexdigest()
            })
        return items
    except:
        return []

def store(items):
    """Store items - dedup built in"""
    stored = 0
    for item in items:
        try:
            DB.execute(
                "INSERT INTO items (hash, title, url, content, time) VALUES (?, ?, ?, ?, ?)",
                (item['hash'], item['title'], item['url'], item['content'], int(time.time()))
            )
            stored += 1
        except sqlite3.IntegrityError:
            pass  # Duplicate
    DB.commit()
    return stored

def get_daily(limit=10):
    """Get today's items"""
    day_ago = int(time.time()) - 86400
    return DB.execute(
        "SELECT title, url, content FROM items WHERE time > ? ORDER BY time DESC LIMIT ?",
        (day_ago, limit)
    ).fetchall()

class Handler(BaseHTTPRequestHandler):
    """HTTP handler - stdlib only"""
    
    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)
        
        if path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head>
                    <title>AttentionSync</title>
                    <style>
                        body { max-width: 800px; margin: 50px auto; font-family: -apple-system, sans-serif; }
                        h1 { color: #333; }
                        .item { margin: 20px 0; padding: 15px; border-left: 3px solid #007aff; }
                        .item h3 { margin: 0 0 10px 0; }
                        .item p { color: #666; margin: 5px 0; }
                        .item a { color: #007aff; text-decoration: none; }
                        input { padding: 10px; width: 300px; }
                        button { padding: 10px 20px; background: #007aff; color: white; border: none; cursor: pointer; }
                    </style>
                </head>
                <body>
                    <h1>AttentionSync</h1>
                    <form action="/add" method="get">
                        <input name="url" placeholder="RSS URL" required>
                        <button>Add Source</button>
                    </form>
                    <h2>Daily Digest</h2>
                    <div id="items"></div>
                    <script>
                        fetch('/daily').then(r => r.json()).then(items => {
                            document.getElementById('items').innerHTML = items.map(item => 
                                `<div class="item">
                                    <h3>${item.title}</h3>
                                    <p>${item.content}</p>
                                    <a href="${item.url}" target="_blank">Read more →</a>
                                </div>`
                            ).join('') || '<p>No items yet. Add an RSS source above.</p>';
                        });
                    </script>
                </body>
                </html>
            """)
            
        elif path == '/add':
            url = query.get('url', [''])[0]
            if url:
                items = fetch_rss(url)
                count = store(items)
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                self.send_response(400)
                self.end_headers()
                
        elif path == '/daily':
            items = [dict(row) for row in get_daily()]
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(items).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Silent

if __name__ == '__main__':
    print("\n AttentionSync - http://localhost:8000\n")
    HTTPServer(('', 8000), Handler).serve_forever()