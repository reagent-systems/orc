"""
Git Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent version control operations, Git workflow management,
and repository coordination capabilities. It operates autonomously within a multi-agent 
workspace, claiming and processing Git-related tasks.
"""

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import BaseTool
from typing import Dict, List
import datetime
import re
import asyncio
import os
import json
import uuid
from datetime import datetime
import subprocess
import shlex

class GitTool(BaseTool):
    """Custom Git tool for the GitAgent"""
    
    def __init__(self):
        super().__init__(
            name="git_operations",
            description="Perform Git version control operations including commits, branches, merges, and status"
        )
    
    async def call(self, operation: str, message: str = None, **kwargs):
        """Execute Git operations"""
        try:
            if operation == "status":
                # Get Git status
                result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    return f"Error: {result.stderr or 'Not a git repository'}"
                
                return {
                    "status": "clean" if not result.stdout.strip() else "modified",
                    "files": result.stdout.strip().split('\n') if result.stdout.strip() else [],
                    "detailed_status": subprocess.run(['git', 'status'], capture_output=True, text=True).stdout
                }
            
            elif operation == "add":
                # Add files to staging
                files = kwargs.get('files', ['.'])
                if isinstance(files, str):
                    files = [files]
                
                cmd = ['git', 'add'] + files
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                return {
                    "success": result.returncode == 0,
                    "command": ' '.join(cmd),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            
            elif operation == "commit":
                # Commit changes
                if not message:
                    return "Error: Commit message required"
                
                cmd = ['git', 'commit', '-m', message]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                return {
                    "success": result.returncode == 0,
                    "command": ' '.join(cmd),
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "commit_hash": self._extract_commit_hash(result.stdout) if result.returncode == 0 else None
                }
            
            elif operation == "branch":
                # Branch operations
                action = kwargs.get('action', 'list')
                branch_name = kwargs.get('branch_name')
                
                if action == 'list':
                    result = subprocess.run(['git', 'branch', '-a'], capture_output=True, text=True, timeout=30)
                    return {
                        "branches": [line.strip().replace('* ', '') for line in result.stdout.split('\n') if line.strip()],
                        "current_branch": self._get_current_branch()
                    }
                
                elif action == 'create':
                    if not branch_name:
                        return "Error: Branch name required for create operation"
                    cmd = ['git', 'checkout', '-b', branch_name]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    return {
                        "success": result.returncode == 0,
                        "command": ' '.join(cmd),
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                
                elif action == 'switch':
                    if not branch_name:
                        return "Error: Branch name required for switch operation"
                    cmd = ['git', 'checkout', branch_name]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    return {
                        "success": result.returncode == 0,
                        "command": ' '.join(cmd),
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
            
            elif operation == "push":
                # Push changes
                remote = kwargs.get('remote', 'origin')
                branch = kwargs.get('branch', self._get_current_branch())
                
                cmd = ['git', 'push', remote, branch]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                return {
                    "success": result.returncode == 0,
                    "command": ' '.join(cmd),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            
            elif operation == "pull":
                # Pull changes
                remote = kwargs.get('remote', 'origin')
                branch = kwargs.get('branch', self._get_current_branch())
                
                cmd = ['git', 'pull', remote, branch]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                return {
                    "success": result.returncode == 0,
                    "command": ' '.join(cmd),
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            
            elif operation == "log":
                # Get commit history
                limit = kwargs.get('limit', 10)
                cmd = ['git', 'log', '--oneline', f'-{limit}']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                return {
                    "commits": result.stdout.strip().split('\n') if result.stdout.strip() else [],
                    "command": ' '.join(cmd)
                }
            
            elif operation == "diff":
                # Show differences
                staged = kwargs.get('staged', False)
                cmd = ['git', 'diff']
                if staged:
                    cmd.append('--staged')
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                return {
                    "diff": result.stdout,
                    "has_changes": bool(result.stdout.strip())
                }
            
            elif operation == "remote":
                # Remote operations
                action = kwargs.get('action', 'list')
                
                if action == 'list':
                    result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=30)
                    return {
                        "remotes": result.stdout.strip().split('\n') if result.stdout.strip() else []
                    }
            
            else:
                return f"Unknown operation: {operation}"
                
        except subprocess.TimeoutExpired:
            return f"Error: Git operation timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _extract_commit_hash(self, stdout: str) -> str:
        """Extract commit hash from git commit output"""
        try:
            # Look for pattern like "[main abc1234]"
            match = re.search(r'\[.*?\s([a-f0-9]+)\]', stdout)
            return match.group(1) if match else None
        except:
            return None
    
    def _get_current_branch(self) -> str:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except:
            return "unknown"


class BaseAgent:
    """Base agent class for multi-agent orchestration system"""
    
    def __init__(self, agent_type: str, capabilities: List[str]):
        self.agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type
        self.capabilities = capabilities
        
        # Three-LLM architecture using proper ADK patterns
        self.executor = LlmAgent(
            name=f"{agent_type}Executor",
            model="gemini-2.0-flash",
            instruction=self.get_executor_instruction(),
            tools=[GitTool()]  # Add git tool to executor
        )
        
        self.evaluator = LlmAgent(
            name=f"{agent_type}Evaluator", 
            model="gemini-2.0-flash",
            instruction=self.get_evaluator_instruction()
        )
        
        self.metacognition = LlmAgent(
            name=f"{agent_type}Metacognition",
            model="gemini-2.0-flash", 
            instruction=self.get_metacognition_instruction()
        )
        
        self.active_tasks = []
        # Workspace should be at project root level, shared by all agents
        self.workspace_path = os.getenv('WORKSPACE_PATH', os.path.join(os.path.dirname(__file__), '..', '..', 'workspace'))
        self.max_concurrent_tasks = int(os.getenv('MAX_CONCURRENT_TASKS', '3'))
        
        # Create runners for LLM execution
        session_service = InMemorySessionService()
        self.executor_runner = Runner(agent=self.executor, app_name=f"{agent_type}_executor", session_service=session_service)
        self.evaluator_runner = Runner(agent=self.evaluator, app_name=f"{agent_type}_evaluator", session_service=session_service)
        self.metacognition_runner = Runner(agent=self.metacognition, app_name=f"{agent_type}_metacognition", session_service=session_service)
    
    def get_threshold(self) -> int:
        """Return eagerness threshold (1-10). Higher = more eager."""
        return 5
    
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

    def get_executor_instruction(self) -> str:
        """Instructions for the executor LLM that does the actual work."""
        raise NotImplementedError
    
    def get_evaluator_instruction(self) -> str:
        """Instructions for the evaluator LLM that decides task fitness."""
        raise NotImplementedError
    
    def get_metacognition_instruction(self) -> str:
        """Instructions for the metacognition LLM that provides self-reflection."""
        raise NotImplementedError
    
    # Main agent loop and other methods (same as other agents)
    async def monitor_workspace(self):
        """Main agent monitoring loop"""
        print(f"🤖 {self.agent_type} starting workspace monitoring...")
        print(f"   Agent ID: {self.agent_id}")
        print(f"   Capabilities: {self.capabilities}")
        print(f"   Workspace: {self.workspace_path}")
        
        while True:
            try:
                await self.update_heartbeat()
                
                pending_tasks = self.scan_pending_tasks()
                
                if pending_tasks:
                    print(f"📋 Found {len(pending_tasks)} pending tasks")
                
                for task_file in pending_tasks:
                    task = self.load_task(task_file)
                    
                    if not self.dependencies_satisfied(task):
                        continue
                    
                    if await self.should_handle(task):
                        print(f"🎯 Attempting to claim task: {task['description'][:50]}...")
                        claimed_file = self.claim_task(task_file)
                            if claimed_file:
                                print(f"✅ Claimed task {task[\'id\'][:8]}...")
                                await self.process_task(claimed_file)
                            break
                
                await asyncio.sleep(self.get_polling_interval())
                
            except Exception as e:
                print(f"❌ Error in monitor loop: {e}")
                await asyncio.sleep(5)
    
    # [All other BaseAgent methods - same implementation]
    def dependencies_satisfied(self, task):
        dependencies = task.get('dependencies', [])
        if not dependencies:
            return True
        
        completed_dir = os.path.join(self.workspace_path, 'tasks', 'completed')
        completed_tasks = set()
        
        if os.path.exists(completed_dir):
            for file in os.listdir(completed_dir):
                if file.endswith('.json'):
                    completed_task = self.load_task(os.path.join(completed_dir, file))
                    completed_tasks.add(completed_task['id'])
        
        return all(dep_id in completed_tasks for dep_id in dependencies)
    
    async def should_handle(self, task):
        try:
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                return False
            
            reflection = await self.metacognitive_check(task)
            if not reflection['proceed']:
                return False
            
            if not await self.can_handle(task):
                return False
            
            score = await self.calculate_fitness_score(task)
            return score >= self.get_threshold()
        except Exception as e:
            print(f"❌ Error in should_handle: {e}")
            return False
    
    async def can_handle(self, task):
        try:
            requirements = task.get('requirements', [])
            if requirements and not any(req in self.capabilities for req in requirements):
                return False
            
            prompt = f"""
            Task: {task['description']}
            Type: {task.get('type', 'unknown')}
            Requirements: {requirements}
            My capabilities: {self.capabilities}
            
            Can I technically execute this task? Answer YES or NO only.
            """
            
            response = await self._run_llm_query(self.evaluator_runner, prompt)
            return "YES" in response.upper()
        except Exception as e:
            return False
    
    async def calculate_fitness_score(self, task):
        try:
            prompt = f"""
            Task: {task['description']}
            Current workload: {len(self.active_tasks)} tasks
            My specialization: {self.agent_type}
            
            Rate my fitness for this task (1-10). Return only the number.
            """
            
            response = await self._run_llm_query(self.evaluator_runner, prompt)
            match = re.search(r'\d+', response)
            return int(match.group()) if match else 1
        except:
            return 1
    
    async def metacognitive_check(self, task):
        try:
            prompt = f"""
            I'm considering taking this task: {task['description']}
            
            Should I take this task? Consider:
            1. Have I done something similar recently?
            2. Will this advance the goal?
            3. Is this a safe Git operation?
            
            Decision: PROCEED or STEP_BACK
            """
            
            response = await self._run_llm_query(self.metacognition_runner, prompt)
            return {
                'proceed': "PROCEED" in response.upper(), 
                'reasoning': response
            }
        except:
            return {'proceed': True, 'reasoning': 'Error in reflection'}
    
    def claim_task(self, task_file: str) -> str:
        try:
            active_dir = os.path.join(self.workspace_path, 'tasks', 'active')
            os.makedirs(active_dir, exist_ok=True)
            
            task_name = os.path.basename(task_file)
            claimed_file = os.path.join(active_dir, f"{self.agent_id}_{task_name}")
            
            os.rename(task_file, claimed_file)
            self.active_tasks.append(claimed_file)
            
            return claimed_file
        except (OSError, FileNotFoundError):
            return None
    
    async def process_task(self, task_file):
        try:
            task = self.load_task(task_file)
            print(f"🔥 Processing task: {task['description']}")
            
            result = await self._run_llm_query(self.executor_runner, f"""
            Task to execute: {task['description']}
            Task type: {task.get('type', 'unknown')}
            Context: {task.get('context', {})}
            
            Please complete this task and provide the results.
            """)
            
            if await self.validates_goal_progress(task, result):
                self.complete_task(task_file, result)
            else:
                self.fail_task(task_file, "Result doesn't advance original goal")
        except Exception as e:
            self.fail_task(task_file, f"Processing error: {str(e)}")
        finally:
            if task_file in self.active_tasks:
                self.active_tasks.remove(task_file)
    
    async def validates_goal_progress(self, task, result):
        try:
            original_goal = task.get('context', {}).get('original_goal')
            if not original_goal:
                return True
            
            response = await self._run_llm_query(self.metacognition_runner, f"""
            Original goal: {original_goal}
            Task result: {result}
            
            Does this result advance the original goal? YES or NO.
            """)
            
            return "YES" in response.upper()
        except:
            return True
    
    def complete_task(self, task_file, result):
        try:
            task = self.load_task(task_file)
            task['result'] = result
            task['completed_at'] = datetime.utcnow().isoformat()
            task['status'] = 'completed'
            
            completed_dir = os.path.join(self.workspace_path, 'tasks', 'completed')
            os.makedirs(completed_dir, exist_ok=True)
            
            completed_file = os.path.join(completed_dir, os.path.basename(task_file))
            self.save_task(completed_file, task)
            
            os.remove(task_file)
            self.save_result_to_context(task, result)
        except Exception as e:
            print(f"❌ Error completing task: {e}")
    
    def fail_task(self, task_file, error_message):
        try:
            task = self.load_task(task_file)
            task['error'] = error_message
            task['failed_at'] = datetime.utcnow().isoformat()
            task['status'] = 'failed'
            
            failed_dir = os.path.join(self.workspace_path, 'tasks', 'failed')
            os.makedirs(failed_dir, exist_ok=True)
            
            failed_file = os.path.join(failed_dir, os.path.basename(task_file))
            self.save_task(failed_file, task)
            
            os.remove(task_file)
        except Exception as e:
            print(f"❌ Error failing task: {e}")
    
    def scan_pending_tasks(self):
        pending_dir = os.path.join(self.workspace_path, 'tasks', 'pending')
        if not os.path.exists(pending_dir):
            return []
        
        return [
            os.path.join(pending_dir, f) 
            for f in os.listdir(pending_dir) 
            if f.endswith('.json')
        ]
    
    def load_task(self, task_file):
        with open(task_file, 'r') as f:
            return json.load(f)
    
    def save_task(self, task_file, task):
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
    
    def get_polling_interval(self):
        import random
        base_interval = int(os.getenv('POLLING_INTERVAL', '2'))
        return base_interval + random.uniform(-0.5, 0.5)
    
    async def update_heartbeat(self):
        try:
            agents_dir = os.path.join(self.workspace_path, 'agents')
            os.makedirs(agents_dir, exist_ok=True)
            
            heartbeat_file = os.path.join(agents_dir, f"{self.agent_id}.json")
            
            status = {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "capabilities": self.capabilities,
                "active_tasks": len(self.active_tasks),
                "last_heartbeat": datetime.utcnow().isoformat(),
                "status": "running"
            }
            
            with open(heartbeat_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"❌ Error updating agent heartbeat: {e}")
    
    def save_result_to_context(self, task, result):
        try:
            context_dir = os.path.join(self.workspace_path, 'context')
            os.makedirs(context_dir, exist_ok=True)
            
            context_file = os.path.join(context_dir, f"{task['id']}_context.json")
            context_data = {
                "task_id": task['id'],
                "description": task['description'],
                "result": result,
                "created_at": datetime.utcnow().isoformat(),
                "original_goal": task.get('context', {}).get('original_goal')
            }
            
            with open(context_file, 'w') as f:
                json.dump(context_data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving context: {e}")


class GitAgent(BaseAgent):
    """Git Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("GitAgent", ["version_control", "git_operations", "repository_management"])
        self.git_tool = GitTool()
    
    def get_threshold(self) -> int:
        return 8  # Very eager for Git operations
    
    def get_executor_instruction(self) -> str:
        return """You are a Git version control specialist that handles all Git operations and workflows.
        
        Core responsibilities:
        - Perform Git operations using the git_operations tool
        - Manage commits, branches, merges, and repository workflows
        - Handle version control tasks and repository management
        - Monitor repository status and coordinate with development workflows
        
        For multi-agent system tasks:
        - Commit changes made by other agents
        - Create and manage feature branches
        - Handle merges and pull requests
        - Maintain clean Git history and workflows
        
        Git operations available:
        - status: Check repository status and modified files
        - add: Stage files for commit
        - commit: Create commits with meaningful messages
        - branch: List, create, or switch branches
        - push/pull: Synchronize with remote repositories
        - log: View commit history
        - diff: Show file differences
        - remote: Manage remote repositories
        
        Best practices:
        - Always check status before making changes
        - Write clear, descriptive commit messages
        - Create feature branches for new work
        - Verify changes before committing
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate Git and version control tasks for the GitAgent.
        
        I can handle tasks requiring:
        - Git operations (commit, branch, merge, push, pull)
        - Repository management and organization
        - Version control workflows
        - Code change tracking and history management
        
        Rate task fitness (1-10) based on:
        - How well it matches Git operation needs
        - Repository state and safety considerations
        - Current workload capacity
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for GitAgent decisions.
        
        Before taking Git tasks, consider:
        - Is the repository in a safe state for this operation?
        - Will this change conflict with ongoing work?
        - Should I check for uncommitted changes first?
        - Is this the right branch for this operation?
        - Am I following proper Git workflow practices?
        
        For version control operations:
        - Are there any merge conflicts to resolve?
        - Is this change ready to be committed?
        - Should I create a feature branch instead?
        - Will this operation affect other developers?
        
        Prioritize repository safety and clean Git history.
        """


# Create the main git agent for this module
git_agent = GitAgent()

# Keep compatibility with ADK patterns
root_agent = git_agent.executor 