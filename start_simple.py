#!/usr/bin/env python3
"""
Linus-style startup: Direct, simple, no bullshit.
"Complexity is the enemy. Simplicity is the goal."
"""

import os
import sys
import subprocess
from pathlib import Path

def ensure_env():
    """Create minimal .env if missing - no magic, just defaults"""
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write("""# Minimal configuration - everything else has sane defaults
ENVIRONMENT=development
DATABASE_URL=sqlite:///./attentionsync.db
SECRET_KEY=dev-secret-key-change-in-production
""")
        print("✓ Created .env with defaults")

def ensure_deps():
    """Install only what we actually need - no feature detection nonsense"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
    except ImportError:
        print("Installing core dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-q",
            "fastapi", "uvicorn", "sqlalchemy", "python-dotenv", "pydantic"
        ])

def main():
    """Just start the damn thing"""
    print("AttentionSync - Starting...")
    
    # Step 1: Ensure basics
    ensure_env()
    ensure_deps()
    
    # Step 2: Start the API - no "smart" detection, no "enhanced" versions
    os.chdir("api")
    
    import uvicorn
    uvicorn.run(
        "app.main:app",  # One app, one entry point
        host="127.0.0.1",
        port=8000,
        reload=True,  # Always reload in dev
        log_level="info"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)