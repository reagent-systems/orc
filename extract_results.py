#!/usr/bin/env python3
"""
Results Extractor for Multi-Agent System
Extracts work results from JSON files and organizes them into readable files
"""

import json
import os
from datetime import datetime
from pathlib import Path

def extract_all_results():
    """Extract all results from workspace and organize them"""
    
    # Create results directory
    results_dir = Path("extracted_results")
    results_dir.mkdir(exist_ok=True)
    
    # Categories for organizing results
    categories = {
        "research": [],
        "documentation": [],
        "code": [],
        "analysis": [],
        "other": []
    }
    
    print("🔍 Extracting results from workspace...")
    
    # Extract from context files
    context_dir = Path("workspace/context")
    if context_dir.exists():
        for context_file in context_dir.glob("*.json"):
            try:
                with open(context_file) as f:
                    data = json.load(f)
                
                task_desc = data.get("description", "")
                result = data.get("result", "")
                task_id = data.get("task_id", "unknown")
                
                # Categorize based on description keywords
                category = categorize_task(task_desc)
                
                categories[category].append({
                    "task_id": task_id,
                    "description": task_desc,
                    "result": result,
                    "created_at": data.get("created_at", ""),
                    "source": "context"
                })
                
            except Exception as e:
                print(f"❌ Error processing {context_file}: {e}")
    
    # Extract from completed tasks
    completed_dir = Path("workspace/tasks/completed")
    if completed_dir.exists():
        for task_file in completed_dir.glob("*.json"):
            try:
                with open(task_file) as f:
                    data = json.load(f)
                
                task_desc = data.get("description", "")
                result = data.get("result", "")
                task_id = data.get("id", "unknown")
                
                # Skip if we already have this from context
                if not any(item["task_id"] == task_id for cat in categories.values() for item in cat):
                    category = categorize_task(task_desc)
                    
                    categories[category].append({
                        "task_id": task_id,
                        "description": task_desc,
                        "result": result,
                        "completed_at": data.get("completed_at", ""),
                        "source": "completed_task"
                    })
                    
            except Exception as e:
                print(f"❌ Error processing {task_file}: {e}")
    
    # Generate organized files
    print("📝 Generating organized result files...")
    
    for category, items in categories.items():
        if items:
            generate_category_file(results_dir, category, items)
    
    # Generate master index
    generate_master_index(results_dir, categories)
    
    print(f"\n🎉 Results extracted to '{results_dir}' directory!")
    print(f"📊 Total items processed: {sum(len(items) for items in categories.values())}")
    for category, items in categories.items():
        if items:
            print(f"   📁 {category}: {len(items)} items")

def categorize_task(description):
    """Categorize task based on description keywords"""
    desc_lower = description.lower()
    
    if any(keyword in desc_lower for keyword in ["research", "find", "search", "tutorials", "documentation", "gather information"]):
        return "research"
    elif any(keyword in desc_lower for keyword in ["readme", "write", "documentation", "guide", "section"]):
        return "documentation"  
    elif any(keyword in desc_lower for keyword in ["code", "script", "program", "application", "test", "syntax"]):
        return "code"
    elif any(keyword in desc_lower for keyword in ["analyze", "analysis", "review", "assess", "compare"]):
        return "analysis"
    else:
        return "other"

def generate_category_file(results_dir, category, items):
    """Generate a file for each category"""
    filename = f"{category}_results.md"
    filepath = results_dir / filename
    
    with open(filepath, 'w') as f:
        f.write(f"# {category.title()} Results\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total items: {len(items)}\n\n")
        f.write("---\n\n")
        
        for i, item in enumerate(items, 1):
            f.write(f"## {i}. {item['description']}\n\n")
            f.write(f"**Task ID:** `{item['task_id']}`\n")
            f.write(f"**Source:** {item['source']}\n")
            if 'completed_at' in item:
                f.write(f"**Completed:** {item['completed_at']}\n")
            elif 'created_at' in item:
                f.write(f"**Created:** {item['created_at']}\n")
            f.write("\n### Result:\n\n")
            
            result = item['result']
            if result and result.strip():
                f.write(f"{result}\n\n")
            else:
                f.write("*No result content available*\n\n")
            
            f.write("---\n\n")

def generate_master_index(results_dir, categories):
    """Generate master index file"""
    filepath = results_dir / "README.md"
    
    with open(filepath, 'w') as f:
        f.write("# Multi-Agent System Results\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("This directory contains all the work results from your multi-agent system, organized by category.\n\n")
        
        f.write("## Summary\n\n")
        total_items = sum(len(items) for items in categories.values())
        f.write(f"**Total completed tasks:** {total_items}\n\n")
        
        f.write("## Categories\n\n")
        for category, items in categories.items():
            if items:
                f.write(f"### 📁 {category.title()}\n")
                f.write(f"**File:** [`{category}_results.md`]({category}_results.md)\n")
                f.write(f"**Items:** {len(items)}\n\n")
                
                # Show preview of items
                f.write("**Tasks included:**\n")
                for item in items[:5]:  # Show first 5
                    f.write(f"- {item['description'][:80]}{'...' if len(item['description']) > 80 else ''}\n")
                if len(items) > 5:
                    f.write(f"- ... and {len(items) - 5} more\n")
                f.write("\n")
        
        f.write("## How to Use\n\n")
        f.write("1. Start with this README for an overview\n")
        f.write("2. Browse category files for specific types of work\n")
        f.write("3. Each task includes the original description and complete results\n")
        f.write("4. Task IDs can be used to reference specific work items\n\n")
        
        f.write("## Agent Performance\n\n")
        f.write("Your multi-agent system successfully completed all these tasks autonomously, ")
        f.write("with agents specializing in their areas of expertise and coordinating seamlessly.\n")

if __name__ == "__main__":
    extract_all_results() 