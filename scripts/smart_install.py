#!/usr/bin/env python3
"""
Smart dependency installer - Linus style: intelligent, interactive, efficient
"The best installer knows what you need before you do."
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Set
import json

def detect_user_intent() -> Set[str]:
    """Detect what features user likely wants based on environment"""
    intent = set()
    
    # Check environment variables for AI keys
    if os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"):
        intent.add("ai")
        print("🤖 AI API keys detected - AI features recommended")
    
    # Check if this looks like a data science environment
    try:
        import numpy
        intent.add("ml")
        print("🧠 NumPy detected - ML features recommended")
    except ImportError:
        pass
    
    # Check if running in development
    if os.getenv("ENVIRONMENT", "development") == "development":
        intent.add("dev")
        print("🛠️  Development environment - dev tools recommended")
    
    # Check for media files in project
    project_root = Path.cwd()
    media_extensions = {'.jpg', '.png', '.pdf', '.docx'}
    media_files = []
    
    for ext in media_extensions:
        files = list(project_root.rglob(f"*{ext}"))
        media_files.extend(files)
    
    if media_files:
        intent.add("media")
        print(f"📁 Media files detected ({len(media_files)} files) - media processing recommended")
    
    return intent


def get_feature_groups() -> Dict[str, Dict[str, any]]:
    """Define feature groups with metadata"""
    return {
        "ai": {
            "name": "AI Services",
            "packages": ["anthropic>=0.7.8", "openai>=1.3.8"],
            "size_mb": 50,
            "install_time": "30s",
            "description": "Claude and GPT integration for smart summarization"
        },
        "ml": {
            "name": "Machine Learning", 
            "packages": ["sentence-transformers>=3.1.0", "scikit-learn>=1.5.0", "numpy>=1.25.2"],
            "size_mb": 800,
            "install_time": "3-5min",
            "description": "Semantic embeddings and clustering algorithms"
        },
        "media": {
            "name": "Media Processing",
            "packages": ["pillow>=10.3.0", "pypdf>=4.0.1"],
            "size_mb": 100,
            "install_time": "1min", 
            "description": "Image and document processing capabilities"
        },
        "dev": {
            "name": "Development Tools",
            "packages": ["ruff>=0.1.9", "pytest>=7.4.3", "mypy>=1.7.1"],
            "size_mb": 30,
            "install_time": "20s",
            "description": "Code quality and testing tools"
        },
        "data": {
            "name": "Data Analysis",
            "packages": ["pandas>=2.1.4"],
            "size_mb": 200,
            "install_time": "1-2min",
            "description": "Heavy data processing and analysis"
        }
    }


def interactive_selection() -> Set[str]:
    """Interactive feature selection"""
    print("\n🎯 AttentionSync Smart Installer")
    print("=" * 40)
    
    # Detect user intent
    detected = detect_user_intent()
    if detected:
        print(f"\n🔍 Detected likely needs: {', '.join(detected)}")
    
    # Show available groups
    groups = get_feature_groups()
    print(f"\n📦 Available feature groups:")
    
    for group_id, group_info in groups.items():
        status = "✅ Recommended" if group_id in detected else "⚪ Optional"
        print(f"  {group_id:8} - {group_info['name']:20} ({group_info['size_mb']:3}MB, {group_info['install_time']:6}) {status}")
        print(f"           {group_info['description']}")
    
    print(f"\n💡 Options:")
    print(f"  all     - Install everything (may take 5-10 minutes)")
    print(f"  auto    - Install recommended features only")
    print(f"  custom  - Choose specific features")
    print(f"  none    - Skip optional features (core only)")
    
    while True:
        choice = input(f"\n🤔 What would you like to install? [auto]: ").strip().lower()
        
        if not choice or choice == "auto":
            return detected
        elif choice == "all":
            return set(groups.keys())
        elif choice == "none":
            return set()
        elif choice == "custom":
            return _custom_selection(groups, detected)
        elif choice in groups:
            return {choice}
        else:
            print(f"❌ Invalid choice: {choice}")


def _custom_selection(groups: Dict[str, Dict], detected: Set[str]) -> Set[str]:
    """Custom feature selection"""
    selected = set()
    
    print(f"\n🎛️  Custom selection (y/n for each):")
    
    for group_id, group_info in groups.items():
        recommended = " (recommended)" if group_id in detected else ""
        default = "y" if group_id in detected else "n"
        
        while True:
            choice = input(f"  Install {group_info['name']}?{recommended} [{default}]: ").strip().lower()
            
            if not choice:
                choice = default
            
            if choice in ("y", "yes", "1", "true"):
                selected.add(group_id)
                break
            elif choice in ("n", "no", "0", "false"):
                break
            else:
                print(f"    Please enter y or n")
    
    return selected


def install_features(selected_groups: Set[str], force: bool = False) -> bool:
    """Install selected feature groups"""
    if not selected_groups:
        print("✅ No optional features selected - core functionality ready")
        return True
    
    groups = get_feature_groups()
    
    # Calculate total size and time
    total_size = sum(groups[group]["size_mb"] for group in selected_groups)
    max_time = max(groups[group]["install_time"] for group in selected_groups)
    
    print(f"\n📊 Installation summary:")
    print(f"  Features: {', '.join(groups[g]['name'] for g in selected_groups)}")
    print(f"  Total size: ~{total_size}MB")
    print(f"  Estimated time: ~{max_time}")
    
    if not force:
        confirm = input(f"\n🚀 Proceed with installation? [y]: ").strip().lower()
        if confirm and confirm not in ("y", "yes", "1", "true"):
            print("❌ Installation cancelled")
            return False
    
    # Install each group
    success_count = 0
    for group_id in selected_groups:
        group = groups[group_id]
        print(f"\n📦 Installing {group['name']}...")
        
        try:
            packages = group["packages"]
            cmd = [sys.executable, "-m", "pip", "install", "--break-system-packages", "--user"] + packages
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"✅ {group['name']} installed successfully")
                success_count += 1
            else:
                print(f"❌ {group['name']} installation failed")
                print(f"   Error: {result.stderr.strip()}")
        
        except subprocess.TimeoutExpired:
            print(f"⏰ {group['name']} installation timed out")
        except Exception as e:
            print(f"💥 {group['name']} installation error: {e}")
    
    print(f"\n📊 Installation complete: {success_count}/{len(selected_groups)} groups")
    
    if success_count == len(selected_groups):
        print("🎉 All features installed successfully!")
        return True
    else:
        print("⚠️  Some features failed to install - check errors above")
        return False


def create_requirements_file(selected_groups: Set[str], output_file: str):
    """Create custom requirements file based on selection"""
    groups = get_feature_groups()
    
    lines = [
        "# AttentionSync Custom Requirements",
        "# Generated by smart_install.py",
        f"# Selected groups: {', '.join(selected_groups)}",
        "",
        "# Core dependencies (always required)",
        "-r requirements-minimal.txt",
        ""
    ]
    
    for group_id in selected_groups:
        group = groups[group_id]
        lines.append(f"# {group['name']} - {group['description']}")
        lines.extend(group["packages"])
        lines.append("")
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"📝 Custom requirements saved to {output_file}")


def check_current_installation() -> Dict[str, bool]:
    """Check what's currently installed"""
    groups = get_feature_groups()
    status = {}
    
    print("🔍 Checking current installation...")
    
    for group_id, group_info in groups.items():
        all_available = True
        for package in group_info["packages"]:
            package_name = package.split(">=")[0].replace("-", "_")
            try:
                __import__(package_name)
            except ImportError:
                all_available = False
                break
        
        status[group_id] = all_available
        status_icon = "✅" if all_available else "❌"
        print(f"  {status_icon} {group_info['name']}")
    
    return status


def main():
    """Main installer function"""
    parser = argparse.ArgumentParser(description="Smart dependency installer for AttentionSync")
    parser.add_argument("--auto", action="store_true", help="Auto-install recommended features")
    parser.add_argument("--all", action="store_true", help="Install all features")
    parser.add_argument("--groups", nargs="+", help="Install specific groups")
    parser.add_argument("--check", action="store_true", help="Check current installation")
    parser.add_argument("--requirements", help="Generate requirements file")
    parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    args = parser.parse_args()
    
    if args.check:
        check_current_installation()
        return True
    
    # Determine what to install
    if args.all:
        selected = set(get_feature_groups().keys())
    elif args.groups:
        selected = set(args.groups)
    elif args.auto:
        selected = detect_user_intent()
    else:
        selected = interactive_selection()
    
    # Generate requirements file if requested
    if args.requirements:
        create_requirements_file(selected, args.requirements)
        return True
    
    # Install selected features
    success = install_features(selected, args.force)
    
    if success and selected:
        print(f"\n🎉 Installation complete!")
        print(f"🚀 Start enhanced API with: python3 app/main_enhanced.py")
        print(f"🔍 Check features with: curl http://localhost:8000/api/v1/features/status")
    
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n👋 Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Installation failed: {e}")
        sys.exit(1)