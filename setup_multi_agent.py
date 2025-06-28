#!/usr/bin/env python3
"""
Multi-Agent Orchestration System Setup

This script sets up the shared workspace and environment for the multi-agent system.
"""

import os
import sys
from pathlib import Path

def create_workspace_structure():
    """Create the shared workspace structure"""
    workspace_path = Path("workspace")
    
    folders = [
        "tasks/pending",
        "tasks/active", 
        "tasks/completed",
        "tasks/failed", 
        "agents",
        "context",
        "results"
    ]
    
    print("🏗️  Creating workspace structure...")
    for folder in folders:
        folder_path = workspace_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {folder_path}")
    
    print(f"\n📁 Workspace created at: {workspace_path.absolute()}")

def setup_environment():
    """Set up environment configuration"""
    env_template = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists():
        if env_template.exists():
            import shutil
            shutil.copy2(env_template, env_file)
            print(f"📄 Copied environment template to: {env_file.absolute()}")
            print("   ⚠️  Please edit .env and add your API keys!")
        else:
            print(f"❌ Template not found: {env_template}")
            print("   💡 You can copy from: google-search-agent/env.example")
    else:
        print(f"📄 Environment file already exists: {env_file.absolute()}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    try:
        import google.adk
        print("   ✅ google-adk installed")
    except ImportError:
        print("   ❌ google-adk not installed")
        print("      Run: pip install google-adk")
        return False
    
    try:
        import dotenv
        print("   ✅ python-dotenv installed")
    except ImportError:
        print("   💡 python-dotenv not installed (recommended)")
        print("      Run: pip install python-dotenv")
    
    return True

def main():
    """Main setup function"""
    print("🚀 Multi-Agent Orchestration System Setup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)
    
    # Create workspace
    create_workspace_structure()
    
    # Setup environment
    setup_environment()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Test the SearchAgent:")
    print("   cd google-search-agent")
    print("   python3 create_test_task.py")
    print("   python3 run_autonomous.py")
    
    print("\n🏗️  Project structure:")
    print("   .env                     # Shared environment config")
    print("   workspace/               # Shared workspace for all agents")
    print("   └── tasks/pending/       # Tasks waiting to be claimed")
    print("   google-search-agent/     # SearchAgent implementation")

if __name__ == "__main__":
    main() 