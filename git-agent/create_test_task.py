#!/usr/bin/env python3
"""
Test Task Creator for GitAgent

This script creates sample Git and version control tasks to test the autonomous GitAgent.
"""

import json
import os
import uuid
from datetime import datetime

def create_test_task(description: str, task_type: str = "git_operations", requirements: list = None):
    """Create a test task JSON file"""
    
    if requirements is None:
        requirements = ["version_control"]
    
    task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "type": task_type,
        "requirements": requirements,
        "priority": "medium",
        "context": {
            "original_goal": "Test the GitAgent functionality",
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
    """Create various test tasks for GitAgent"""
    print("🧪 Creating test tasks for GitAgent...")
    print("=" * 40)
    
    # Test tasks of different types
    test_tasks = [
        {
            "description": "Check the current Git repository status and list any modified files",
            "requirements": ["version_control", "git_operations"]
        },
        {
            "description": "Stage all changes and commit them with a meaningful message",
            "requirements": ["git_operations"]
        },
        {
            "description": "Create a new feature branch called 'test-feature'",
            "requirements": ["version_control", "git_operations"]
        },
        {
            "description": "Show the last 5 commits in the repository history",
            "requirements": ["git_operations"]
        },
        {
            "description": "Display the differences between staged and unstaged files",
            "requirements": ["version_control", "git_operations"]
        },
        {
            "description": "List all branches in the repository including remote branches",
            "requirements": ["git_operations", "repository_management"]
        },
        {
            "description": "Switch to the main branch and pull latest changes",
            "requirements": ["version_control", "git_operations"]
        },
        {
            "description": "Check remote repository configuration and status",
            "requirements": ["repository_management", "git_operations"]
        }
    ]
    
    for i, task_info in enumerate(test_tasks, 1):
        print(f"\n{i}. Creating task: {task_info['description'][:50]}...")
        
        create_test_task(
            task_info['description'], 
            requirements=task_info['requirements']
        )
    
    print(f"\n🎉 Created {len(test_tasks)} test tasks!")
    print("\nTo test the GitAgent:")
    print("1. Make sure your .env file has Google API keys")
    print("2. Ensure you're in a Git repository (or run 'git init')")
    print("3. Run: python3 run_autonomous.py")
    print("4. Watch the agent claim and process these Git tasks")
    print("\n🔧 Git operations covered:")
    print("   - Repository status checking")
    print("   - Staging and committing changes")
    print("   - Branch management")
    print("   - Commit history")
    print("   - File differences")
    print("   - Remote repository operations")

if __name__ == "__main__":
    main() 