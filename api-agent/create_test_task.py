#!/usr/bin/env python3
"""
Test Task Creator for APIAgent

This script creates sample API testing and HTTP operation tasks to test the autonomous APIAgent.
"""

import json
import os
import uuid
from datetime import datetime

def create_test_task(description: str, task_type: str = "api_operations", requirements: list = None):
    """Create a test task JSON file"""
    
    if requirements is None:
        requirements = ["api_testing"]
    
    task = {
        "id": str(uuid.uuid4()),
        "description": description,
        "type": task_type,
        "requirements": requirements,
        "priority": "medium",
        "context": {
            "original_goal": "Test the APIAgent functionality",
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
    """Create various test tasks for APIAgent"""
    print("🧪 Creating test tasks for APIAgent...")
    print("=" * 40)
    
    # Test tasks of different types
    test_tasks = [
        {
            "description": "Make a GET request to httpbin.org/get and validate the response",
            "requirements": ["api_testing", "http_requests"]
        },
        {
            "description": "Test a JSON API endpoint and validate the response structure",
            "requirements": ["api_testing", "integration_testing"]
        },
        {
            "description": "Perform a health check on a public API endpoint",
            "requirements": ["api_testing"]
        },
        {
            "description": "Make a POST request with JSON data to httpbin.org/post",
            "requirements": ["api_testing", "http_requests"]
        },
        {
            "description": "Test multiple API endpoints in a batch operation",
            "requirements": ["api_testing", "integration_testing"]
        },
        {
            "description": "Validate a sample webhook payload structure",
            "requirements": ["webhook_handling", "api_testing"]
        },
        {
            "description": "Test API endpoint response times and performance",
            "requirements": ["api_testing", "integration_testing"]
        },
        {
            "description": "Parse and validate a GitHub webhook payload",
            "requirements": ["webhook_handling"]
        },
        {
            "description": "Test API error handling and status code validation",
            "requirements": ["api_testing", "integration_testing"]
        },
        {
            "description": "Perform comprehensive API integration testing with validation",
            "requirements": ["api_testing", "integration_testing", "http_requests"]
        }
    ]
    
    for i, task_info in enumerate(test_tasks, 1):
        print(f"\n{i}. Creating task: {task_info['description'][:50]}...")
        
        create_test_task(
            task_info['description'], 
            requirements=task_info['requirements']
        )
    
    print(f"\n🎉 Created {len(test_tasks)} test tasks!")
    print("\nTo test the APIAgent:")
    print("1. Make sure your .env file has Google API keys")
    print("2. Ensure you have internet connectivity for API tests")
    print("3. Run: python3 run_autonomous.py")
    print("4. Watch the agent claim and process these API tasks")
    print("\n🌐 API operations covered:")
    print("   - HTTP requests (GET, POST, PUT, DELETE)")
    print("   - API endpoint testing and validation")
    print("   - JSON response parsing and validation")
    print("   - Webhook payload processing")
    print("   - Batch API testing")
    print("   - Health checks and performance testing")
    print("   - Error handling and status code validation")

if __name__ == "__main__":
    main() 