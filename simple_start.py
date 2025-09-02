#!/usr/bin/env python3
"""
AttentionSync - Linus Style: One file to rule them all.
"Talk is cheap. Show me the code."
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import feedparser
import httpx

# === Configuration (10 lines, not 103) ===
DATABASE = os.getenv("DATABASE", "attentionsync.db")
API_KEY = os.getenv("API_KEY", "dev-key-change-in-production")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "").lower() == "true"

# === Database (Simple is better) ===
def get_db():
    """One connection, no pools, no magic"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables - once, simple"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            url TEXT,
            content TEXT,
            summary TEXT,
            hash TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            url TEXT NOT NULL,
            type TEXT DEFAULT 'rss',
            active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

# === Models (Data structures, not abstractions) ===
class User(BaseModel):
    email: str
    password: str

class Source(BaseModel):
    url: str
    type: str = "rss"

class Content(BaseModel):
    title: str
    url: str
    content: str
    summary: Optional[str] = None

# === Core Functions (Do one thing well) ===
def hash_password(password: str) -> str:
    """Hash password - simple SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def hash_content(content: str) -> str:
    """Hash content for deduplication"""
    return hashlib.sha256(content.encode()).hexdigest()

def summarize(text: str, max_length: int = 200) -> str:
    """First N characters - good enough"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def fetch_rss(url: str) -> List[Dict]:
    """Fetch RSS feed - no async complexity"""
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:10]:  # Last 10 items
            items.append({
                'title': entry.get('title', 'Untitled'),
                'url': entry.get('link', ''),
                'content': entry.get('summary', ''),
                'published': entry.get('published', datetime.now())
            })
        return items
    except Exception as e:
        print(f"RSS fetch failed: {e}")
        return []

# === API (FastAPI, but simple) ===
app = FastAPI(title="AttentionSync", version="1.0")

# CORS - for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if DEBUG else ["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    """Initialize on startup"""
    init_db()

@app.get("/")
def root():
    """Health check"""
    return {"status": "running", "name": "AttentionSync"}

@app.post("/register")
def register(user: User):
    """Register user - simple"""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (user.email, hash_password(user.password))
        )
        conn.commit()
        return {"message": "User created"}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "User already exists")
    finally:
        conn.close()

@app.post("/login")
def login(user: User):
    """Login - return simple token"""
    conn = get_db()
    result = conn.execute(
        "SELECT id FROM users WHERE email = ? AND password_hash = ?",
        (user.email, hash_password(user.password))
    ).fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(401, "Invalid credentials")
    
    # Simple token - in production use JWT
    token = hashlib.sha256(f"{user.email}:{API_KEY}".encode()).hexdigest()
    return {"token": token, "user_id": result[0]}

@app.post("/sources")
def add_source(source: Source, user_id: int = 1):  # Default user for simplicity
    """Add content source"""
    conn = get_db()
    conn.execute(
        "INSERT INTO sources (user_id, url, type) VALUES (?, ?, ?)",
        (user_id, source.url, source.type)
    )
    conn.commit()
    conn.close()
    return {"message": "Source added"}

@app.get("/sources")
def list_sources(user_id: int = 1):
    """List user sources"""
    conn = get_db()
    sources = conn.execute(
        "SELECT * FROM sources WHERE user_id = ? AND active = 1",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(s) for s in sources]

@app.post("/fetch")
def fetch_content(user_id: int = 1):
    """Fetch content from all sources"""
    conn = get_db()
    sources = conn.execute(
        "SELECT * FROM sources WHERE user_id = ? AND active = 1",
        (user_id,)
    ).fetchall()
    
    total_items = 0
    for source in sources:
        if source['type'] == 'rss':
            items = fetch_rss(source['url'])
            for item in items:
                content_hash = hash_content(item['content'])
                try:
                    conn.execute("""
                        INSERT INTO contents (user_id, title, url, content, summary, hash)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        item['title'],
                        item['url'],
                        item['content'],
                        summarize(item['content']),
                        content_hash
                    ))
                    total_items += 1
                except sqlite3.IntegrityError:
                    pass  # Duplicate, skip
    
    conn.commit()
    conn.close()
    return {"fetched": total_items}

@app.get("/contents")
def get_contents(user_id: int = 1, limit: int = 10):
    """Get recent contents"""
    conn = get_db()
    contents = conn.execute("""
        SELECT * FROM contents 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(c) for c in contents]

@app.get("/daily")
def daily_digest(user_id: int = 1):
    """Get daily digest - top 10 items"""
    conn = get_db()
    contents = conn.execute("""
        SELECT title, url, summary FROM contents 
        WHERE user_id = ? 
        AND date(created_at) = date('now')
        ORDER BY created_at DESC 
        LIMIT 10
    """, (user_id,)).fetchall()
    conn.close()
    
    if not contents:
        return {"message": "No content for today. Run /fetch first."}
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "count": len(contents),
        "items": [dict(c) for c in contents]
    }

# === Main ===
if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════╗
    ║     AttentionSync - Simple Start     ║
    ╠══════════════════════════════════════╣
    ║  "Perfection is achieved not when    ║
    ║   there is nothing more to add,      ║
    ║   but when there is nothing left     ║
    ║   to take away." - Antoine de Saint  ║
    ╚══════════════════════════════════════╝
    
    Starting on http://localhost:{PORT}
    """)
    
    uvicorn.run(
        "simple_start:app",
        host="0.0.0.0",
        port=PORT,
        reload=DEBUG
    )