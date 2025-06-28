#!/usr/bin/env python3
"""
Test Task Creator for TestAgent

This script creates sample testing and quality assurance tasks to test the autonomous TestAgent.
"""

import json
import os
import uuid
from datetime import datetime

def create_test_task(description: str, task_type: str = "test_operations", requirements: list = None):
    """Create a test task JSON file"""
    
    if requirements is None:
        requirements = ["test_execution"]
    
    task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "type": task_type,
        "requirements": requirements,
        "priority": "medium",
        "context": {
            "original_goal": "Test the TestAgent functionality",
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
    """Create various test tasks for TestAgent"""
    print("🧪 Creating test tasks for TestAgent...")
    print("=" * 40)
    
    # Test tasks of different types
    test_tasks = [
        {
            "description": "Discover available test files and testing frameworks in the project",
            "requirements": ["test_execution", "quality_assurance"]
        },
        {
            "description": "Run all available unit tests with pytest framework",
            "requirements": ["test_execution"]
        },
        {
            "description": "Generate a test file template for a Python module",
            "requirements": ["test_generation", "test_execution"]
        },
        {
            "description": "Execute code coverage analysis and generate coverage report",
            "requirements": ["test_execution", "quality_assurance"]
        },
        {
            "description": "Run code quality checks using available linting tools",
            "requirements": ["quality_assurance"]
        },
        {
            "description": "Check for available testing dependencies and tools",
            "requirements": ["test_execution"]
        },
        {
            "description": "Run unittest framework tests and provide detailed results",
            "requirements": ["test_execution"]
        },
        {
            "description": "Perform comprehensive quality assurance check including tests and linting",
            "requirements": ["test_execution", "quality_assurance", "test_generation"]
        }
    ]
    
    for i, task_info in enumerate(test_tasks, 1):
        print(f"\n{i}. Creating task: {task_info['description'][:50]}...")
        
        create_test_task(
            task_info['description'], 
            requirements=task_info['requirements']
        )
    
    print(f"\n🎉 Created {len(test_tasks)} test tasks!")
    print("\nTo test the TestAgent:")
    print("1. Make sure your .env file has Google API keys")
    print("2. Optionally install testing tools: pip install pytest coverage flake8")
    print("3. Run: python3 run_autonomous.py")
    print("4. Watch the agent claim and process these testing tasks")
    print("\n🔧 Testing operations covered:")
    print("   - Test discovery and framework detection")
    print("   - Test execution (pytest, unittest)")
    print("   - Test generation and template creation")
    print("   - Code coverage analysis")
    print("   - Code quality and linting checks")
    print("   - Testing tool dependency checking")

if __name__ == "__main__":
    main() 