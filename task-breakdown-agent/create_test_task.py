#!/usr/bin/env python3
"""
Test Task Creator for TaskBreakdownAgent

This script creates sample complex tasks to test the autonomous TaskBreakdownAgent's
decomposition and orchestration capabilities.
"""

import json
import os
import uuid
from datetime import datetime

def create_test_task(description: str, task_type: str = "complex_goal", requirements: list = None):
    """Create a test task JSON file"""
    
    if requirements is None:
        requirements = ["task_decomposition"]
    
    task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "type": task_type,
        "requirements": requirements,
        "priority": "high",
        "context": {
            "original_goal": description,
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
    """Create various complex test tasks for TaskBreakdownAgent"""
    print("🧪 Creating complex test tasks for TaskBreakdownAgent...")
    print("=" * 50)
    
    # Complex test tasks that require decomposition
    complex_tasks = [
        {
            "description": "Research Python web frameworks, analyze their features, and create a comparison document",
            "requirements": ["task_decomposition", "orchestration"]
        },
        {
            "description": "Set up a new Python project with virtual environment, install dependencies, and create a hello world web app",
            "requirements": ["task_decomposition", "planning"]
        },
        {
            "description": "Analyze the codebase for syntax errors, research solutions, and fix all identified issues",
            "requirements": ["task_decomposition", "orchestration", "planning"]
        },
        {
            "description": "Create a comprehensive README for this multi-agent system including architecture overview, setup instructions, and usage examples",
            "requirements": ["task_decomposition", "orchestration"]
        },
        {
            "description": "Research best practices for multi-agent systems, analyze current implementation, and suggest improvements",
            "requirements": ["task_decomposition", "planning"]
        },
        {
            "description": "Set up automated testing for all agents, create test cases, and generate a testing report",
            "requirements": ["task_decomposition", "orchestration", "planning"]
        }
    ]
    
    # Simple tasks that shouldn't need breakdown (for comparison)
    simple_tasks = [
        {
            "description": "List files in the current directory",
            "requirements": ["command_execution"]
        },
        {
            "description": "Search for 'Python best practices' on Google",
            "requirements": ["web_search"]
        }
    ]
    
    print("Creating COMPLEX tasks (should trigger breakdown):")
    print("-" * 30)
    for i, task_info in enumerate(complex_tasks, 1):
        print(f"\n{i}. Creating complex task: {task_info['description'][:60]}...")
        create_test_task(
            task_info['description'], 
            task_type="complex_goal",
            requirements=task_info['requirements']
        )
    
    print(f"\n\nCreating SIMPLE tasks (should NOT trigger breakdown):")
    print("-" * 30)
    for i, task_info in enumerate(simple_tasks, 1):
        print(f"\n{i}. Creating simple task: {task_info['description'][:60]}...")
        create_test_task(
            task_info['description'], 
            task_type="simple_task",
            requirements=task_info['requirements']
        )
    
    total_tasks = len(complex_tasks) + len(simple_tasks)
    print(f"\n🎉 Created {total_tasks} test tasks!")
    print(f"   - {len(complex_tasks)} complex tasks (should be broken down)")
    print(f"   - {len(simple_tasks)} simple tasks (should be passed to specialists)")
    
    print("\nTo test the TaskBreakdownAgent:")
    print("1. Make sure your .env file has Google API keys")
    print("2. Run: python3 run_autonomous.py")
    print("3. Watch the agent decide which tasks to break down vs pass through")
    print("4. Check the workspace/tasks/pending/ for generated subtasks")

if __name__ == "__main__":
    main() 