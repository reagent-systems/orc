#!/usr/bin/env python3
"""
Create test tasks for Google Sheets Agent

This script creates sample tasks that demonstrate the GoogleSheetsAgent's
capabilities including data analysis, reporting, and business intelligence.
"""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path

def create_test_tasks():
    """Create various test tasks for GoogleSheetsAgent"""
    
    # Get workspace path
    project_root = Path(__file__).parent.parent
    workspace_path = project_root / 'workspace'
    pending_dir = workspace_path / 'tasks' / 'pending'
    
    # Create directories if they don't exist
    pending_dir.mkdir(parents=True, exist_ok=True)
    
    # Test tasks for GoogleSheetsAgent
    test_tasks = [
        {
            "description": "Generate a business intelligence report analyzing the performance of all agents in the multi-agent system",
            "type": "reporting",
            "requirements": ["business_intelligence", "data_analysis"],
            "priority": "high",
            "context": {
                "original_goal": "Create comprehensive performance analytics for the multi-agent system",
                "data_source": "workspace completed tasks",
                "report_type": "executive summary"
            }
        },
        {
            "description": "Create a KPI dashboard showing total tasks completed, success rates, and agent utilization metrics",
            "type": "spreadsheet_operations",
            "requirements": ["reporting", "data_analysis"],
            "priority": "high",
            "context": {
                "original_goal": "Provide real-time visibility into system performance",
                "dashboard_type": "KPI metrics",
                "update_frequency": "daily"
            }
        },
        {
            "description": "Sync all completed agent tasks to a structured spreadsheet format for tracking and analysis",
            "type": "data_analysis",
            "requirements": ["spreadsheet_operations"],
            "priority": "medium",
            "context": {
                "original_goal": "Maintain comprehensive task tracking database",
                "sync_scope": "all completed tasks",
                "format": "structured data"
            }
        },
        {
            "description": "Analyze task completion patterns and generate recommendations for optimizing agent performance",
            "type": "business_intelligence",
            "requirements": ["data_analysis", "reporting"],
            "priority": "medium",
            "context": {
                "original_goal": "Optimize multi-agent system efficiency",
                "analysis_type": "performance optimization",
                "output": "actionable recommendations"
            }
        },
        {
            "description": "Create a report template for monthly multi-agent system performance reviews",
            "type": "reporting",
            "requirements": ["spreadsheet_operations"],
            "priority": "low",
            "context": {
                "original_goal": "Standardize performance reporting",
                "template_type": "monthly review",
                "sections": ["executive summary", "metrics", "recommendations"]
            }
        }
    ]
    
    created_tasks = []
    
    for task_data in test_tasks:
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create complete task structure
        task = {
            "id": task_id,
            "description": task_data["description"],
            "type": task_data["type"],
            "requirements": task_data["requirements"],
            "dependencies": [],
            "priority": task_data["priority"],
            "context": task_data["context"],
            "created_at": datetime.utcnow().isoformat(),
            "max_retries": 3,
            "retry_count": 0
        }
        
        # Save task to pending directory
        task_file = pending_dir / f"{task_id}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        created_tasks.append({
            "id": task_id,
            "description": task_data["description"][:60] + "..." if len(task_data["description"]) > 60 else task_data["description"],
            "type": task_data["type"],
            "file": str(task_file)
        })
        
        print(f"📋 Created task: {task_data['description'][:50]}...")
    
    return created_tasks

def main():
    """Main function"""
    print("🚀 Creating test tasks for GoogleSheetsAgent...")
    print("="*60)
    
    try:
        tasks = create_test_tasks()
        
        print(f"\n✅ Successfully created {len(tasks)} test tasks:")
        print()
        
        for i, task in enumerate(tasks, 1):
            print(f"{i}. {task['description']}")
            print(f"   Type: {task['type']}")
            print(f"   ID: {task['id'][:8]}...")
            print()
        
        print("🎯 Tasks are now available in the workspace for GoogleSheetsAgent to process!")
        print("\nTo run the agent:")
        print("cd google-sheets-agent && python3 run_autonomous.py")
        
    except Exception as e:
        print(f"❌ Error creating test tasks: {e}")
        raise

if __name__ == "__main__":
    main() 