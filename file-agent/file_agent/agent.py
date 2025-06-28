"""
File Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent file operations, code analysis, and agent generation
capabilities. It operates autonomously within a multi-agent workspace, claiming and 
processing file-related tasks.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool
from typing import Dict, List
import datetime
import re
import asyncio
import os
import json
import uuid
from datetime import datetime
import shutil
from pathlib import Path

class FileSystemTool(BaseTool):
    """Custom file system tool for the FileAgent"""
    
    def __init__(self):
        super().__init__(
            name="file_operations",
            description="Perform file system operations including read, write, create, delete files and directories"
        )
    
    async def call(self, operation: str, path: str, content: str = None, **kwargs):
        """Execute file system operations"""
        try:
            if operation == "read":
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif operation == "write":
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"File written to {path}"
            
            elif operation == "append":
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return f"Content appended to {path}"
            
            elif operation == "delete":
                if os.path.isfile(path):
                    os.remove(path)
                    return f"File {path} deleted"
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    return f"Directory {path} deleted"
                else:
                    return f"Path {path} not found"
            
            elif operation == "create_dir":
                os.makedirs(path, exist_ok=True)
                return f"Directory {path} created"
            
            elif operation == "list":
                if os.path.isdir(path):
                    items = os.listdir(path)
                    return f"Contents of {path}: {items}"
                else:
                    return f"Directory {path} not found"
            
            elif operation == "exists":
                return str(os.path.exists(path))
            
            elif operation == "copy":
                dest = kwargs.get('destination')
                if os.path.isfile(path):
                    shutil.copy2(path, dest)
                    return f"File copied from {path} to {dest}"
                elif os.path.isdir(path):
                    shutil.copytree(path, dest)
                    return f"Directory copied from {path} to {dest}"
                else:
                    return f"Source {path} not found"
            
            else:
                return f"Unknown operation: {operation}"
                
        except Exception as e:
            return f"Error: {str(e)}"


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
            tools=[FileSystemTool()]  # Add file tool to executor
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
    
    def get_threshold(self) -> int:
        """Return eagerness threshold (1-10). Higher = more eager."""
        return 5
    
    def get_executor_instruction(self) -> str:
        """Instructions for the executor LLM that does the actual work."""
        raise NotImplementedError
    
    def get_evaluator_instruction(self) -> str:
        """Instructions for the evaluator LLM that decides task fitness."""
        raise NotImplementedError
    
    def get_metacognition_instruction(self) -> str:
        """Instructions for the metacognition LLM that provides self-reflection."""
        raise NotImplementedError
    
    # Main agent loop
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
                    
                    # Check dependencies first
                    if not self.dependencies_satisfied(task):
                        print(f"⏳ Task {task['id'][:8]}... waiting for dependencies")
                        continue
                    
                    if await self.should_handle(task):
                        print(f"🎯 Attempting to claim task: {task['description'][:50]}...")
                        if self.claim_task(task_file):
                            print(f"✅ Claimed task {task['id'][:8]}...")
                            await self.process_task(task_file)
                            break
                
                await asyncio.sleep(self.get_polling_interval())
                
            except Exception as e:
                print(f"❌ Error in monitor loop: {e}")
                await asyncio.sleep(5)
    
    def dependencies_satisfied(self, task) -> bool:
        """Check if all task dependencies are completed"""
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
    
    # LLM-based decision making
    async def should_handle(self, task) -> bool:
        """Strategic decision with metacognition, capability check, and scoring"""
        try:
            # Check concurrent task limit
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                return False
            
            # Metacognitive reflection first
            reflection = await self.metacognitive_check(task)
            if not reflection['proceed']:
                print(f"🧠 Metacognition says skip: {reflection['reasoning'][:50]}...")
                return False
            
            # Capability check
            if not await self.can_handle(task):
                return False
            
            # Fitness scoring
            score = await self.calculate_fitness_score(task)
            print(f"📊 Fitness score: {score}/{self.get_threshold()}")
            return score >= self.get_threshold()
        
        except Exception as e:
            print(f"❌ Error in should_handle: {e}")
            return False
    
    async def can_handle(self, task) -> bool:
        """Binary capability check"""
        try:
            # Check requirements match capabilities
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
            
            response = await self.evaluator.process(prompt)
            can_do = "YES" in response.upper()
            print(f"🔧 Can handle: {can_do}")
            return can_do
        
        except Exception as e:
            print(f"❌ Error in can_handle: {e}")
            return False
    
    async def calculate_fitness_score(self, task) -> int:
        """Calculate fitness score 1-10"""
        try:
            prompt = f"""
            Task: {task['description']}
            Current workload: {len(self.active_tasks)} tasks
            My specialization: {self.agent_type}
            Task priority: {task.get('priority', 'medium')}
            
            Rate my fitness for this task (1-10). Consider:
            - How well it matches my specialization
            - Current workload capacity
            - Task priority
            
            Return only the number.
            """
            
            response = await self.evaluator.process(prompt)
            match = re.search(r'\d+', response)
            return int(match.group()) if match else 1
        
        except Exception as e:
            print(f"❌ Error calculating fitness: {e}")
            return 1
    
    async def metacognitive_check(self, task) -> Dict:
        """Internal reflection on whether to take this task"""
        try:
            recent_actions = self.get_recent_actions()
            workspace_state = self.get_workspace_summary()
            
            prompt = f"""
            I'm considering taking this task: {task['description']}
            
            My recent actions: {recent_actions}
            Current workspace state: {workspace_state}
            Original goal: {task.get('context', {}).get('original_goal')}
            
            Internal reflection:
            1. Have I done something similar recently?
            2. Will this actually progress the goal?
            3. Am I creating redundant work?
            4. Should I step back and let others handle this?
            
            Decision: PROCEED or STEP_BACK
            Reasoning: [brief explanation]
            """
            
            response = await self.metacognition.process(prompt)
            return {
                'proceed': "PROCEED" in response.upper(), 
                'reasoning': response
            }
        
        except Exception as e:
            print(f"❌ Error in metacognitive check: {e}")
            return {'proceed': True, 'reasoning': 'Error in reflection'}
    
    # Atomic task claiming
    def claim_task(self, task_file: str) -> bool:
        """Atomically claim a task using os.rename()"""
        try:
            active_dir = os.path.join(self.workspace_path, 'tasks', 'active')
            os.makedirs(active_dir, exist_ok=True)
            
            task_name = os.path.basename(task_file)
            claimed_file = os.path.join(active_dir, f"{self.agent_id}_{task_name}")
            
            # Atomic operation
            os.rename(task_file, claimed_file)
            self.active_tasks.append(claimed_file)
            
            # Update task with claim info
            task = self.load_task(claimed_file)
            task['claimed_by'] = self.agent_id
            task['claimed_at'] = datetime.utcnow().isoformat()
            self.save_task(claimed_file, task)
            
            return True
        
        except (OSError, FileNotFoundError):
            # Another agent claimed it first
            return False
    
    # Task processing with goal validation
    async def process_task(self, task_file: str):
        """Process a claimed task with error handling"""
        try:
            task = self.load_task(task_file)
            print(f"🔥 Processing task: {task['description']}")
            
            # Update heartbeat periodically during processing
            self.update_task_heartbeat(task_file)
            
            # Execute the actual task
            result = await self.executor.process(f"""
            Task to execute: {task['description']}
            Task type: {task.get('type', 'unknown')}
            Context: {task.get('context', {})}
            
            Please complete this task and provide the results.
            """)
            
            # Validate result advances original goal
            if await self.validates_goal_progress(task, result):
                print(f"✅ Task completed successfully")
                self.complete_task(task_file, result)
            else:
                print(f"❌ Task result doesn't advance original goal")
                self.fail_task(task_file, "Result doesn't advance original goal")
        
        except Exception as e:
            print(f"❌ Error processing task: {e}")
            self.fail_task(task_file, f"Processing error: {str(e)}")
        
        finally:
            # Remove from active tasks
            if task_file in self.active_tasks:
                self.active_tasks.remove(task_file)
    
    def update_task_heartbeat(self, task_file: str):
        """Update task heartbeat to show progress"""
        try:
            task = self.load_task(task_file)
            task['last_heartbeat'] = datetime.utcnow().isoformat()
            task['heartbeat_count'] = task.get('heartbeat_count', 0) + 1
            self.save_task(task_file, task)
        except Exception as e:
            print(f"❌ Error updating heartbeat: {e}")
    
    async def validates_goal_progress(self, task, result) -> bool:
        """Validate that result advances the original goal"""
        try:
            original_goal = task.get('context', {}).get('original_goal')
            if not original_goal:
                return True
            
            prompt = f"""
            Original goal: {original_goal}
            Task completed: {task['description']}
            Task result: {result}
            
            Does this result meaningfully advance the original goal? 
            Answer YES or NO with brief reasoning.
            """
            
            response = await self.metacognition.process(prompt)
            return "YES" in response.upper()
        
        except Exception as e:
            print(f"❌ Error validating goal progress: {e}")
            return True  # Default to accepting result
    
    def complete_task(self, task_file: str, result):
        """Move task to completed with results"""
        try:
            task = self.load_task(task_file)
            task['result'] = result
            task['completed_at'] = datetime.utcnow().isoformat()
            task['status'] = 'completed'
            
            # Move to completed folder
            completed_dir = os.path.join(self.workspace_path, 'tasks', 'completed')
            os.makedirs(completed_dir, exist_ok=True)
            
            completed_file = os.path.join(completed_dir, os.path.basename(task_file))
            self.save_task(completed_file, task)
            
            # Remove from active
            os.remove(task_file)
            
            # Save result to context for future tasks
            self.save_result_to_context(task, result)
            
        except Exception as e:
            print(f"❌ Error completing task: {e}")
    
    def fail_task(self, task_file: str, error_message: str):
        """Move task to failed with error details"""
        try:
            task = self.load_task(task_file)
            task['error'] = error_message
            task['failed_at'] = datetime.utcnow().isoformat()
            task['status'] = 'failed'
            task['retry_count'] = task.get('retry_count', 0) + 1
            
            # Check if we should retry
            if task['retry_count'] < task.get('max_retries', 3):
                # Move back to pending for retry
                pending_dir = os.path.join(self.workspace_path, 'tasks', 'pending')
                retry_file = os.path.join(pending_dir, f"retry_{os.path.basename(task_file)}")
                self.save_task(retry_file, task)
                print(f"🔄 Task queued for retry ({task['retry_count']}/3)")
            else:
                # Move to failed folder
                failed_dir = os.path.join(self.workspace_path, 'tasks', 'failed')
                os.makedirs(failed_dir, exist_ok=True)
                
                failed_file = os.path.join(failed_dir, os.path.basename(task_file))
                self.save_task(failed_file, task)
                print(f"💀 Task failed permanently")
            
            # Remove from active
            os.remove(task_file)
            
        except Exception as e:
            print(f"❌ Error failing task: {e}")
    
    # Utility methods
    def scan_pending_tasks(self) -> List[str]:
        """Scan for pending tasks"""
        pending_dir = os.path.join(self.workspace_path, 'tasks', 'pending')
        if not os.path.exists(pending_dir):
            return []
        
        return [
            os.path.join(pending_dir, f) 
            for f in os.listdir(pending_dir) 
            if f.endswith('.json')
        ]
    
    def load_task(self, task_file: str) -> Dict:
        """Load task from JSON file"""
        with open(task_file, 'r') as f:
            return json.load(f)
    
    def save_task(self, task_file: str, task: Dict):
        """Save task to JSON file"""
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
    
    def get_polling_interval(self) -> int:
        """Get polling interval with some randomization"""
        import random
        base_interval = int(os.getenv('POLLING_INTERVAL', '2'))
        return base_interval + random.uniform(-0.5, 0.5)
    
    async def update_heartbeat(self):
        """Update agent heartbeat file"""
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
    
    def get_recent_actions(self) -> List[str]:
        """Get summary of recent actions for metacognition"""
        # Simple implementation - could be enhanced to track actual history
        return [f"Active tasks: {len(self.active_tasks)}"]
    
    def get_workspace_summary(self) -> str:
        """Get current workspace state summary"""
        try:
            pending = len(self.scan_pending_tasks())
            return f"Pending tasks: {pending}, My active: {len(self.active_tasks)}"
        except:
            return "workspace summary unavailable"
    
    def save_result_to_context(self, task, result):
        """Save task result to context for future use"""
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


class FileAgent(BaseAgent):
    """File Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("FileAgent", ["file_operations", "code_analysis", "text_processing", "agent_generation"])
        self.filesystem_tool = FileSystemTool()
    
    def get_threshold(self) -> int:
        return 8  # Very eager for file operations
    
    def get_executor_instruction(self) -> str:
        return """You are a file operations specialist that handles all file system tasks and code generation.
        
        Core responsibilities:
        - Read, write, create, delete files and directories using the file_operations tool
        - Code analysis and syntax checking
        - Text processing and content extraction
        - Generate new agent code when needed for the multi-agent system
        - Code refactoring and formatting
        
        For multi-agent system tasks:
        - Generate new agent code based on specifications and research
        - Create proper ADK agent implementations with BaseAgent inheritance
        - Set up agent directory structures and configuration files
        - Process code files and perform analysis
        
        Always:
        - Use the file_operations tool for all file system operations
        - Validate file operations and provide clear feedback
        - Follow proper code structure and ADK patterns when generating agents
        - Ensure generated code follows the multi-agent architecture (BaseAgent, three-LLM system)
        
        Available operations: read, write, append, delete, create_dir, list, exists, copy
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate file and code tasks for the FileAgent.
        
        I can handle tasks requiring:
        - File system operations (read, write, create, delete)
        - Code analysis and generation
        - Text processing and document handling
        - Agent code generation for the multi-agent system
        - Directory management and file organization
        
        Rate task fitness (1-10) based on:
        - How well it matches file/code operation needs
        - Complexity of file operations required
        - Current workload capacity
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for FileAgent decisions.
        
        Before taking file tasks, consider:
        - Is this file operation safe and necessary?
        - Will this advance the goal effectively?
        - Am I duplicating existing work or files?
        - Should I validate file contents before making changes?
        
        For code generation:
        - Do I have enough specifications to generate quality code?
        - Will the generated code follow proper ADK patterns?
        - Should I reference existing agent implementations?
        
        Prioritize data safety and goal advancement.
        """


# Create the main file agent for this module
file_agent = FileAgent()

# Keep compatibility with ADK patterns
root_agent = file_agent.executor 