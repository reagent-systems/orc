#!/usr/bin/env python3
"""
Test Task Creator for FileAgent

This script creates sample file operation tasks to test the autonomous FileAgent.
"""

import json
import os
import uuid
from datetime import datetime

def create_test_task(description: str, task_type: str = "file_operations", requirements: list = None):
    """Create a test task JSON file"""
    
    if requirements is None:
        requirements = ["file_operations"]
    
    task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "type": task_type,
        "requirements": requirements,
        "priority": "medium",
        "context": {
            "original_goal": "Test the FileAgent functionality",
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
    """Create various test tasks for FileAgent"""
    print("🧪 Creating test tasks for FileAgent...")
    print("=" * 40)
    
    # Test tasks of different types
    test_tasks = [
        "Create a simple Python hello world script",
        "Read and analyze the structure of an existing Python file",
        "Create a new directory structure for a Python project",
        "Generate a README.md file with project documentation",
        "Copy a file to a backup location with timestamp",
        "Create a configuration JSON file with default settings",
        "Analyze code quality and suggest improvements",
        "Generate a new agent based on specifications"
    ]
    
    for i, description in enumerate(test_tasks, 1):
        print(f"\n{i}. Creating task: {description[:50]}...")
        
        # Set specific requirements for different task types
        if "agent" in description.lower():
            requirements = ["file_operations", "code_analysis", "agent_generation"]
        elif "analyze" in description.lower():
            requirements = ["file_operations", "code_analysis"]
        else:
            requirements = ["file_operations"]
            
        create_test_task(description, requirements=requirements)
    
    print(f"\n🎉 Created {len(test_tasks)} test tasks!")
    print("\nTo test the FileAgent:")
    print("1. Make sure your .env file has Google API keys")
    print("2. Run: python3 run_autonomous.py")
    print("3. Watch the agent claim and process these tasks")

if __name__ == "__main__":
    main() 