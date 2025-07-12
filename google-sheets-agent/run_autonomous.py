#!/usr/bin/env python3
"""
Google Sheets Agent - Autonomous Operation

This script runs the Google Sheets Agent in autonomous mode, where it continuously
monitors the shared workspace for tasks related to spreadsheet operations,
data analysis, reporting, and business intelligence.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the path so we can import our agent
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from project root
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"📁 Loaded .env from: {env_path}")
else:
    print(f"⚠️  No .env file found at: {env_path}")

# Set workspace path to project root level
workspace_path = project_root / 'workspace'
os.environ['WORKSPACE_PATH'] = str(workspace_path)

# Create workspace directories if they don't exist
for subdir in ['tasks/pending', 'tasks/active', 'tasks/completed', 'tasks/failed', 'agents', 'context', 'results']:
    (workspace_path / subdir).mkdir(parents=True, exist_ok=True)
    print(f"📁 Created folder: {workspace_path / subdir}")

from sheets_agent.agent import google_sheets_agent

async def main():
    """Main function to run the Google Sheets Agent autonomously"""
    print("🤖 Starting GoogleSheetsAgent in autonomous mode...")
    print("="*50)
    
    try:
        # Start the agent's workspace monitoring loop
        await google_sheets_agent.monitor_workspace()
    except KeyboardInterrupt:
        print("\n🛑 GoogleSheetsAgent stopped by user")
    except Exception as e:
        print(f"❌ Error running GoogleSheetsAgent: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 