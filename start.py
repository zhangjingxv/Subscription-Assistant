#!/usr/bin/env python3
"""
Ultimate one-click startup - Linus style: zero friction, maximum intelligence
"The best software just works. No manual, no configuration, no frustration."
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def main():
    """Ultimate startup - just make it work!"""
    print("🚀 AttentionSync One-Click Startup")
    print("=" * 35)
    print("⚡ Analyzing environment...")
    
    # Step 1: Auto-configure if needed
    if not Path(".env").exists():
        print("🔧 Auto-configuring environment...")
        subprocess.run([sys.executable, "scripts/zero_config_start.py", "--skip-install"], 
                      cwd=Path.cwd(), timeout=10)
    
    # Step 2: Ensure minimal dependencies
    try:
        import fastapi
        print("✅ Core dependencies available")
    except ImportError:
        print("📦 Installing core dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "--break-system-packages", "--user",
            "-r", "api/requirements-minimal.txt"
        ], timeout=300)
    
    # Step 3: Auto-install recommended features
    print("🤖 Auto-installing recommended features...")
    subprocess.run([
        sys.executable, "scripts/smart_install.py", "--auto", "--force"
    ], cwd=Path.cwd())
    
    # Step 4: Start the application
    print("🚀 Starting AttentionSync...")
    
    # Choose the best available app version
    try:
        from api.app.core.smart_deps import get_dependency_manager
        os.chdir("api")
        
        manager = get_dependency_manager()
        manager.scan_environment()
        features = manager.create_feature_flags()
        
        if sum(features.values()) > 2:
            print("🎯 Starting Enhanced API (multiple features available)")
            app_module = "app.main_enhanced:app"
        else:
            print("🎯 Starting Minimal API (basic features only)")
            app_module = "app.main_minimal:app"
        
    except Exception:
        print("🎯 Starting Minimal API (fallback)")
        os.chdir("api")
        app_module = "app.main_minimal:app"
    
    # Start with uvicorn
    try:
        import uvicorn
        
        environment = os.getenv("ENVIRONMENT", "development")
        host = "127.0.0.1" if environment == "development" else "0.0.0.0"
        
        print(f"🌐 API will be available at: http://{host}:8000")
        print(f"📚 Documentation at: http://{host}:8000/docs")
        print(f"🎛️  Features at: http://{host}:8000/api/v1/features/status")
        print()
        print("Press Ctrl+C to stop")
        
        uvicorn.run(
            app_module,
            host=host,
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()