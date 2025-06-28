#!/usr/bin/env python3
"""
Test Task Creator for DatabaseAgent

This script creates sample database operation tasks to test the autonomous DatabaseAgent.
"""

import json
import os
import uuid
from datetime import datetime

def create_test_task(description: str, task_type: str = "database_operations", requirements: list = None):
    """Create a test task JSON file"""
    
    if requirements is None:
        requirements = ["database_operations"]
    
    task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "type": task_type,
        "requirements": requirements,
        "priority": "medium",
        "context": {
            "original_goal": "Test the DatabaseAgent functionality",
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
    """Create various test tasks for DatabaseAgent"""
    print("🧪 Creating test tasks for DatabaseAgent...")
    print("=" * 40)
    
    # Test tasks of different types
    test_tasks = [
        {
            "description": "Create a SQLite database connection and verify it works",
            "requirements": ["database_operations"]
        },
        {
            "description": "Create a sample users table with id, name, email, and created_at columns",
            "requirements": ["database_operations", "sql_queries"]
        },
        {
            "description": "Insert sample user data into the users table",
            "requirements": ["database_operations", "sql_queries"]
        },
        {
            "description": "Query all users from the database and display results",
            "requirements": ["database_operations", "sql_queries"]
        },
        {
            "description": "List all tables in the database and describe their structure",
            "requirements": ["database_operations"]
        },
        {
            "description": "Export user data to a CSV file for backup purposes",
            "requirements": ["database_operations", "data_management"]
        },
        {
            "description": "Create a backup of the entire database",
            "requirements": ["database_operations", "data_management"]
        },
        {
            "description": "Get comprehensive database information including size and record counts",
            "requirements": ["database_operations"]
        },
        {
            "description": "Create a products table and import sample data from CSV",
            "requirements": ["database_operations", "data_management", "migrations"]
        },
        {
            "description": "Update user records and verify the changes were applied correctly",
            "requirements": ["database_operations", "sql_queries"]
        }
    ]
    
    for i, task_info in enumerate(test_tasks, 1):
        print(f"\n{i}. Creating task: {task_info['description'][:50]}...")
        
        create_test_task(
            task_info['description'], 
            requirements=task_info['requirements']
        )
    
    print(f"\n🎉 Created {len(test_tasks)} test tasks!")
    print("\nTo test the DatabaseAgent:")
    print("1. Make sure your .env file has Google API keys")
    print("2. Run: python3 run_autonomous.py")
    print("3. Watch the agent claim and process these database tasks")
    print("\n🗄️ Database operations covered:")
    print("   - Database connection management")
    print("   - SQL query execution (CREATE, INSERT, SELECT, UPDATE)")
    print("   - Table schema management")
    print("   - Data import/export (CSV)")
    print("   - Database backup and restore")
    print("   - Database information and statistics")

if __name__ == "__main__":
    main() 