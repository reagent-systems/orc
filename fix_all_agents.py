#!/usr/bin/env python3
"""
Script to fix all agents with the same issues we fixed in SearchAgent:
1. Add ADK Runner infrastructure with proper imports
2. Add _run_llm_query helper method  
3. Fix claim_task method to return file path
4. Replace all .process() calls with _run_llm_query()
5. Fix task processing logic
"""

import os
import re
from pathlib import Path

def fix_agent_file(agent_path):
    """Fix a single agent file"""
    print(f"🔧 Fixing {agent_path}...")
    
    try:
        with open(agent_path, 'r') as f:
            content = f.read()
        
        # 1. Add missing imports after existing ADK imports
        if 'from google.adk.runners import Runner' not in content:
            # Find where to insert the imports
            import_insertion_point = content.find('from google.adk.agents import LlmAgent')
            if import_insertion_point != -1:
                # Insert after the LlmAgent import
                line_end = content.find('\n', import_insertion_point)
                new_imports = '''from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
'''
                content = content[:line_end+1] + new_imports + content[line_end+1:]
        
        # 2. Add ADK Runner infrastructure to BaseAgent __init__
        if '# Create runners for LLM execution' not in content:
            # Find the BaseAgent __init__ method
            baseagent_init = content.find('def __init__(self, agent_type: str, capabilities: List[str]')
            if baseagent_init != -1:
                # Find the end of the existing __init__ method setup
                max_concurrent_line = content.find('self.max_concurrent_tasks = int(os.getenv(\'MAX_CONCURRENT_TASKS\', \'3\'))', baseagent_init)
                if max_concurrent_line != -1:
                    line_end = content.find('\n', max_concurrent_line)
                    runner_code = '''
        
        # Create runners for LLM execution
        session_service = InMemorySessionService()
        self.executor_runner = Runner(agent=self.executor, app_name=f"{agent_type}_executor", session_service=session_service)
        self.evaluator_runner = Runner(agent=self.evaluator, app_name=f"{agent_type}_evaluator", session_service=session_service)
        self.metacognition_runner = Runner(agent=self.metacognition, app_name=f"{agent_type}_metacognition", session_service=session_service)'''
                    content = content[:line_end] + runner_code + content[line_end:]
        
        # 3. Add the _run_llm_query helper method if it doesn't exist
        if 'async def _run_llm_query(self, runner: Runner, prompt: str) -> str:' not in content:
            # Find where to insert it (after get_threshold method)
            threshold_method = content.find('def get_threshold(self) -> int:')
            if threshold_method != -1:
                # Find the end of get_threshold method
                method_end = content.find('\n    def get_', threshold_method + 1)
                if method_end == -1:
                    method_end = content.find('\n    # ', threshold_method + 1)
                
                llm_query_method = '''
    async def _run_llm_query(self, runner: Runner, prompt: str) -> str:
        """Helper method to run LLM queries using proper ADK Runner pattern"""
        try:
            # Create a unique session for this query
            session_id = f"query_{uuid.uuid4().hex[:8]}"
            user_id = f"agent_{self.agent_id}"
            
            # Create session
            session = await runner.session_service.create_session(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id
            )
            
            # Create content and run
            content = types.Content(role='user', parts=[types.Part(text=prompt)])
            events = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
            
            # Collect final response
            final_response = ""
            async for event in events:
                if event.is_final_response() and event.content and event.content.parts:
                    final_response = event.content.parts[0].text or ""
                    break
            
            return final_response
        except Exception as e:
            print(f"❌ Error in LLM query: {e}")
            return f"Error: {str(e)}"
'''
                content = content[:method_end] + llm_query_method + content[method_end:]
        
        # 4. Fix all .process() calls to use _run_llm_query
        content = re.sub(
            r'await self\.evaluator\.process\(([^)]+)\)',
            r'await self._run_llm_query(self.evaluator_runner, \1)',
            content
        )
        content = re.sub(
            r'await self\.metacognition\.process\(([^)]+)\)',
            r'await self._run_llm_query(self.metacognition_runner, \1)',
            content
        )
        content = re.sub(
            r'await self\.executor\.process\(([^)]+)\)',
            r'await self._run_llm_query(self.executor_runner, \1)',
            content
        )
        
        # 5. Fix claim_task method signature and return value
        content = re.sub(
            r'def claim_task\(self, task_file: str\) -> bool:',
            r'def claim_task(self, task_file: str) -> str:',
            content
        )
        content = re.sub(
            r'return True\n(\s+)except \(OSError, FileNotFoundError\):\n(\s+)# Another agent claimed it first\n(\s+)return False',
            r'return claimed_file\n\1except (OSError, FileNotFoundError):\n\2# Another agent claimed it first\n\3return None',
            content
        )
        
        # 6. Fix task processing logic in monitor_workspace
        content = re.sub(
            r'if self\.claim_task\(task_file\):\n(\s+)print\(f"✅ Claimed task \{task\[\'id\'\]\[:8\]\}\.\.\."\)\n(\s+)await self\.process_task\(task_file\)',
            r'claimed_file = self.claim_task(task_file)\n\1if claimed_file:\n\1    print(f"✅ Claimed task {task[\'id\'][:8]}...")\n\1    await self.process_task(claimed_file)',
            content
        )
        
        # Write the fixed content back
        with open(agent_path, 'w') as f:
            f.write(content)
            
        print(f"✅ Fixed {agent_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {agent_path}: {e}")
        return False

def main():
    """Fix all agent files"""
    print("🚀 Fixing all agent files with ADK API and task processing issues...")
    
    # Find all agent files
    agent_dirs = [
        'task-breakdown-agent/task_breakdown_agent',
        'file-agent/file_agent', 
        'terminal-agent/terminal_agent',
        'git-agent/git_agent',
        'test-agent/test_agent',
        'database-agent/database_agent',
        'api-agent/api_agent'
    ]
    
    fixed_count = 0
    total_count = len(agent_dirs)
    
    for agent_dir in agent_dirs:
        agent_file = f"{agent_dir}/agent.py"
        if os.path.exists(agent_file):
            if fix_agent_file(agent_file):
                fixed_count += 1
        else:
            print(f"⚠️  File not found: {agent_file}")
    
    print(f"\n🎉 Fixed {fixed_count}/{total_count} agent files!")
    
    if fixed_count == total_count:
        print("\n✅ All agents now have:")
        print("   - Proper ADK Runner infrastructure")
        print("   - Fixed .process() calls")
        print("   - Corrected task processing logic")
        print("   - Working file path handling")
        print("\n🚀 Your multi-agent system is ready!")
    else:
        print(f"\n⚠️  {total_count - fixed_count} agents still need manual fixing")

if __name__ == "__main__":
    main() 