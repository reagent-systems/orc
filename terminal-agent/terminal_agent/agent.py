"""
Terminal Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent command execution, system operations, and CLI navigation
capabilities. It operates autonomously within a multi-agent workspace, claiming and 
processing terminal-related tasks.
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
import subprocess
import shlex

class TerminalTool(BaseTool):
    """Custom terminal tool for the TerminalAgent"""
    
    def __init__(self):
        super().__init__(
            name="terminal_operations",
            description="Execute terminal commands and system operations"
        )
    
    async def call(self, operation: str, command: str = None, **kwargs):
        """Execute terminal operations"""
        try:
            if operation == "execute":
                # Parse command safely
                if not command:
                    return "Error: No command provided"
                
                # Basic safety checks
                dangerous_commands = ['rm -rf /', 'sudo rm', 'format', 'del /q']
                if any(dangerous in command.lower() for dangerous in dangerous_commands):
                    return f"Error: Potentially dangerous command blocked: {command}"
                
                # Execute command with timeout
                result = subprocess.run(
                    shlex.split(command),
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=kwargs.get('working_directory', os.getcwd())
                )
                
                output = {
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0
                }
                
                return json.dumps(output, indent=2)
            
            elif operation == "check_command":
                # Check if a command exists
                try:
                    subprocess.run(['which', command], check=True, capture_output=True)
                    return f"Command '{command}' is available"
                except subprocess.CalledProcessError:
                    return f"Command '{command}' not found"
            
            elif operation == "get_env":
                # Get environment variable
                env_var = kwargs.get('env_var', command)
                value = os.getenv(env_var)
                return f"{env_var}={value}" if value else f"{env_var} not set"
            
            elif operation == "list_processes":
                # List running processes (safe subset)
                result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                return result.stdout[:2000]  # Limit output
            
            elif operation == "get_system_info":
                # Get basic system information
                commands = {
                    "os": "uname -s",
                    "hostname": "hostname",
                    "user": "whoami",
                    "pwd": "pwd"
                }
                
                info = {}
                for key, cmd in commands.items():
                    try:
                        result = subprocess.run(
                            shlex.split(cmd),
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        info[key] = result.stdout.strip() if result.returncode == 0 else "unknown"
                    except:
                        info[key] = "unknown"
                
                return json.dumps(info, indent=2)
            
            else:
                return f"Unknown operation: {operation}"
                
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after 30 seconds"
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
            tools=[TerminalTool()]  # Add terminal tool to executor
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
    
    # Main agent loop and other methods (same as FileAgent)
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
                        if self.claim_task(task_file):
                            print(f"✅ Claimed task {task['id'][:8]}...")
                            await self.process_task(task_file)
                            break
                
                await asyncio.sleep(self.get_polling_interval())
                
            except Exception as e:
                print(f"❌ Error in monitor loop: {e}")
                await asyncio.sleep(5)
    
    # [All other BaseAgent methods - same implementation as FileAgent]
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
            
            response = await self.evaluator.process(prompt)
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
            
            response = await self.evaluator.process(prompt)
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
            3. Is this command safe to execute?
            
            Decision: PROCEED or STEP_BACK
            """
            
            response = await self.metacognition.process(prompt)
            return {
                'proceed': "PROCEED" in response.upper(), 
                'reasoning': response
            }
        except:
            return {'proceed': True, 'reasoning': 'Error in reflection'}
    
    def claim_task(self, task_file):
        try:
            active_dir = os.path.join(self.workspace_path, 'tasks', 'active')
            os.makedirs(active_dir, exist_ok=True)
            
            task_name = os.path.basename(task_file)
            claimed_file = os.path.join(active_dir, f"{self.agent_id}_{task_name}")
            
            os.rename(task_file, claimed_file)
            self.active_tasks.append(claimed_file)
            
            return True
        except (OSError, FileNotFoundError):
            return False
    
    async def process_task(self, task_file):
        try:
            task = self.load_task(task_file)
            print(f"🔥 Processing task: {task['description']}")
            
            result = await self.executor.process(f"""
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
            
            response = await self.metacognition.process(f"""
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


class TerminalAgent(BaseAgent):
    """Terminal Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("TerminalAgent", ["command_execution", "system_operations", "cli_navigation"])
        self.terminal_tool = TerminalTool()
    
    def get_threshold(self) -> int:
        return 7  # Eager for terminal operations
    
    def get_executor_instruction(self) -> str:
        return """You are a terminal operations specialist that handles command execution and system operations.
        
        Core responsibilities:
        - Execute shell commands safely using the terminal_operations tool
        - System operations and process management
        - Environment setup and package installation
        - Git operations and version control
        - Directory navigation and file management via command line
        
        For multi-agent system tasks:
        - Install dependencies and packages for new agents
        - Set up development environments
        - Execute deployment commands
        - Run tests and build processes
        - Handle system configuration
        
        SAFETY FIRST:
        - Always validate commands before execution
        - Avoid potentially dangerous operations (rm -rf /, sudo rm, etc.)
        - Explain what commands will do before running them
        - Use the terminal_operations tool for all command execution
        
        Available operations: execute, check_command, get_env, list_processes, get_system_info
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate terminal and system tasks for the TerminalAgent.
        
        I can handle tasks requiring:
        - Command execution and shell operations
        - System administration tasks
        - Package management and installation
        - Git and version control operations
        - Environment setup and configuration
        - Process management and monitoring
        
        Rate task fitness (1-10) based on:
        - How well it matches terminal/system operation needs
        - Safety of the commands involved
        - Current workload capacity
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for TerminalAgent decisions.
        
        Before taking terminal tasks, consider:
        - Is this command safe to execute?
        - Will this advance the goal effectively?
        - Do I need elevated permissions?
        - Should I test in a safe environment first?
        - Could this interfere with other running processes?
        
        For system operations:
        - Is the system in a stable state for this operation?
        - Do I have the necessary tools and permissions?
        - Will this change affect other agents or processes?
        
        Prioritize system safety and goal advancement.
        """


# Create the main terminal agent for this module
terminal_agent = TerminalAgent()

# Keep compatibility with ADK patterns
root_agent = terminal_agent.executor 