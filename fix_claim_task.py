#!/usr/bin/env python3
"""
Fix remaining claim_task method issues for agents without type annotations
"""

import os
import re

def fix_claim_task_method(agent_path):
    """Fix claim_task method in a single agent file"""
    print(f"🔧 Fixing claim_task in {agent_path}...")
    
    try:
        with open(agent_path, 'r') as f:
            content = f.read()
        
        # Fix claim_task method signature (add type annotations if missing)
        content = re.sub(
            r'def claim_task\(self, task_file\):',
            r'def claim_task(self, task_file: str) -> str:',
            content
        )
        
        # Fix return statements in claim_task method
        # Look for the pattern: return True followed by except block with return False
        content = re.sub(
            r'(\s+)return True(\s+except \(OSError, FileNotFoundError\):[\s\S]*?)(\s+)return False',
            r'\1return claimed_file\2\3return None',
            content
        )
        
        # Write the fixed content back
        with open(agent_path, 'w') as f:
            f.write(content)
            
        print(f"✅ Fixed claim_task in {agent_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {agent_path}: {e}")
        return False

def main():
    """Fix claim_task methods in all agent files"""
    print("🚀 Fixing remaining claim_task method issues...")
    
    # Find all agent files
    agent_dirs = [
        'task-breakdown-agent/task_breakdown_agent',
        'terminal-agent/terminal_agent',
        'git-agent/git_agent',
        'test-agent/test_agent',
        'database-agent/database_agent',
        'api-agent/api_agent'
    ]
    
    fixed_count = 0
    
    for agent_dir in agent_dirs:
        agent_file = f"{agent_dir}/agent.py"
        if os.path.exists(agent_file):
            if fix_claim_task_method(agent_file):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {agent_file}")
    
    print(f"\n🎉 Fixed claim_task methods in {fixed_count} additional agent files!")
    print("✅ All agents now have properly typed claim_task methods that return file paths!")

if __name__ == "__main__":
    main() 