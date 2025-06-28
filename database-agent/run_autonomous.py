#!/usr/bin/env python3
"""
Autonomous DatabaseAgent Runner

This script starts the DatabaseAgent in autonomous mode, monitoring the workspace
for database operations and data management tasks to claim and process.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the database_agent module to the path
sys.path.insert(0, str(Path(__file__).parent))

from database_agent.agent import database_agent

async def initialize_workspace():
    """Initialize workspace structure if it doesn't exist"""
    # Workspace should be at project root level, shared by all agents
    workspace_path = os.getenv('WORKSPACE_PATH', os.path.join(os.path.dirname(__file__), '..', 'workspace'))
    
    folders = [
        "tasks/pending",
        "tasks/active", 
        "tasks/completed",
        "tasks/failed",
        "agents",
        "context",
        "results"
    ]
    
    for folder in folders:
        folder_path = os.path.join(workspace_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        print(f"📁 Created folder: {folder_path}")

async def main():
    """Main entry point for autonomous DatabaseAgent"""
    print("🤖 Starting DatabaseAgent in autonomous mode...")
    print("=" * 50)
    
    # Initialize workspace
    await initialize_workspace()
    
    # Start workspace monitoring
    try:
        await database_agent.monitor_workspace()
    except KeyboardInterrupt:
        print("\n⏹️  DatabaseAgent shutting down...")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Load .env from project root
    project_root = os.path.join(os.path.dirname(__file__), '..')
    env_file = os.path.join(project_root, '.env')
    
    try:
        from dotenv import load_dotenv
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"📁 Loaded .env from: {env_file}")
        else:
            print(f"💡 No .env found at: {env_file}")
    except ImportError:
        print("💡 Tip: Install python-dotenv for automatic .env loading")
        print("   pip install python-dotenv")
    
    # Check basic setup
    if not os.getenv('GOOGLE_API_KEY') and not os.getenv('GOOGLE_GENAI_USE_VERTEXAI'):
        print("❌ Missing Google API key. Please set up your environment:")
        print(f"   1. Copy .env.example to .env (or use setup_multi_agent.py)")
        print("   2. Add your Google API keys")
        print("   3. Run: python3 run_autonomous.py")
        sys.exit(1)
    
    # Check for SQLite availability (built into Python)
    try:
        import sqlite3
        print("✅ SQLite database support is available")
        
        # Check for CSV support (built into Python)
        import csv
        print("✅ CSV import/export support is available")
        
    except ImportError:
        print("❌ Database support not available")
        sys.exit(1)
    
    print("💡 Database features:")
    print("   - SQLite database operations")
    print("   - SQL query execution")
    print("   - CSV import/export")
    print("   - Database backup and restore")
    print("   - Table schema management")
    
    asyncio.run(main()) 