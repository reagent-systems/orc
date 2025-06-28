#!/usr/bin/env python3
"""
Test Task Creator for TerminalAgent

This script creates sample terminal and system operation tasks to test the autonomous TerminalAgent.
"""

import json
import os
import uuid
from datetime import datetime

def create_test_task(description: str, task_type: str = "terminal_operations", requirements: list = None):
    """Create a test task JSON file"""
    
    if requirements is None:
        requirements = ["command_execution"]
    
    task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "type": task_type,
        "requirements": requirements,
        "priority": "medium",
        "context": {
            "original_goal": "Test the TerminalAgent functionality",
            "test_task": True
        },
        "created_at": datetime.utcnow().isoformat(),
        "max_retries": 3,
        "retry_count": 0
    }
    
    # Create workspace structure at project root level
    workspace_path = os.getenv('WORKSPACE_PATH', os.path.join(os.path.dirname(__file__), '..', 'workspace'))
    pending_dir = os.path.join(workspace_path, 'tasks', 'pending')
    os.makedirs(pending_dir, exist_ok=True)
    
    # Save task file
    task_file = os.path.join(pending_dir, f"{task['id']}.json")
    with open(task_file, 'w') as f:
        json.dump(task, f, indent=2)
    
    print(f"✅ Created test task: {task_file}")
    print(f"   Description: {description}")
    print(f"   Task ID: {task['id']}")
    
    return task

def main():
    """Create various test tasks for TerminalAgent"""
    print("🧪 Creating test tasks for TerminalAgent...")
    print("=" * 40)
    
    # Test tasks of different types
    test_tasks = [
        {
            "description": "Check system information and environment",
            "requirements": ["system_operations"]
        },
        {
            "description": "List files in the current directory",
            "requirements": ["command_execution"]
        },
        {
            "description": "Check if git is installed and available",
            "requirements": ["command_execution"]
        },
        {
            "description": "Get the current working directory and disk usage",
            "requirements": ["system_operations"]
        },
        {
            "description": "List running processes (safe overview)",
            "requirements": ["system_operations"]
        },
        {
            "description": "Check network connectivity with ping",
            "requirements": ["command_execution", "system_operations"]
        },
        {
            "description": "Create a temporary directory for testing",
            "requirements": ["command_execution"]
        },
        {
            "description": "Find Python installation path and version",
            "requirements": ["command_execution"]
        }
    ]
    
    for i, task_info in enumerate(test_tasks, 1):
        print(f"\n{i}. Creating task: {task_info['description'][:50]}...")
        
        create_test_task(
            task_info['description'], 
            requirements=task_info['requirements']
        )
    
    print(f"\n🎉 Created {len(test_tasks)} test tasks!")
    print("\nTo test the TerminalAgent:")
    print("1. Make sure your .env file has Google API keys")
    print("2. Run: python3 run_autonomous.py")
    print("3. Watch the agent claim and process these tasks")
    print("\n🛡️  Safety note: All test commands are safe for system operations")

if __name__ == "__main__":
    main() 