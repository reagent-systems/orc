#!/usr/bin/env python3
"""
Test Task Creator for SearchAgent

This script creates sample search tasks to test the autonomous SearchAgent.
"""

import json
import os
import uuid
from datetime import datetime

def create_test_task(description: str, task_type: str = "search", requirements: list = None):
    """Create a test task JSON file"""
    
    if requirements is None:
        requirements = ["web_search"]
    
    task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "type": task_type,
        "requirements": requirements,
        "priority": "medium",
        "context": {
            "original_goal": "Test the SearchAgent functionality",
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
    """Create various test tasks"""
    print("🧪 Creating test tasks for SearchAgent...")
    print("=" * 40)
    
    # Test tasks of different types
    test_tasks = [
        "Search for the latest Python 3.12 features",
        "Find tutorials on how to use Google's Agent Development Kit",
        "Research recent developments in AI agent frameworks",
        "Look up news about multi-agent systems",
        "Find academic papers on autonomous agent coordination"
    ]
    
    for i, description in enumerate(test_tasks, 1):
        print(f"\n{i}. Creating task: {description[:50]}...")
        create_test_task(description)
    
    print(f"\n🎉 Created {len(test_tasks)} test tasks!")
    print("\nTo test the SearchAgent:")
    print("1. Make sure your .env file has Google API keys")
    print("2. Run: python run_autonomous.py")
    print("3. Watch the agent claim and process these tasks")

if __name__ == "__main__":
    main() 