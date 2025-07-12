"""
Task Breakdown Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent task decomposition and orchestration capabilities.
It takes complex tasks and breaks them down into sequential, actionable steps that
can be handled by specialist agents. It operates autonomously within a multi-agent 
workspace, claiming and processing complex tasks.
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

class TaskAnalysisTool(BaseTool):
    """Custom task analysis tool for the TaskBreakdownAgent"""
    
    def __init__(self):
        super().__init__(
            name="task_analysis",
            description="Analyze tasks and break them down into actionable steps"
        )
    
    async def call(self, operation: str, task_description: str = None, **kwargs):
        """Execute task analysis operations"""
        try:
            if operation == "get_agent_capabilities":
                # Return known agent capabilities from workspace
                workspace_path = kwargs.get('workspace_path', '.')
                agents_dir = os.path.join(workspace_path, 'agents')
                
                capabilities = {
                    "SearchAgent": ["web_search", "google_search", "research"],
                    "FileAgent": ["file_operations", "code_analysis", "text_processing", "agent_generation"],
                    "TerminalAgent": ["command_execution", "system_operations", "cli_navigation"],
                    "TaskBreakdownAgent": ["task_decomposition", "orchestration", "planning"]
                }
                
                # Also check for active agents in workspace
                if os.path.exists(agents_dir):
                    for file in os.listdir(agents_dir):
                        if file.endswith('.json'):
                            try:
                                with open(os.path.join(agents_dir, file), 'r') as f:
                                    agent_info = json.load(f)
                                    agent_type = agent_info.get('agent_type')
                                    agent_caps = agent_info.get('capabilities', [])
                                    if agent_type and agent_caps:
                                        capabilities[agent_type] = agent_caps
                            except:
                                continue
                
                return json.dumps(capabilities, indent=2)
            
            elif operation == "estimate_complexity":
                # Estimate task complexity (1-10)
                if not task_description:
                    return "Error: No task description provided"
                
                # Simple heuristics for complexity
                complexity = 1
                
                if len(task_description.split()) > 20:
                    complexity += 2
                
                high_complexity_keywords = ['analyze', 'generate', 'create', 'build', 'implement', 'deploy', 'configure']
                if any(keyword in task_description.lower() for keyword in high_complexity_keywords):
                    complexity += 3
                
                multi_step_keywords = ['then', 'after', 'next', 'finally', 'once', 'before']
                if any(keyword in task_description.lower() for keyword in multi_step_keywords):
                    complexity += 2
                
                return min(complexity, 10)
            
            elif operation == "check_dependencies":
                # Check if task has implicit dependencies
                dependencies = []
                if not task_description:
                    return json.dumps(dependencies)
                
                task_lower = task_description.lower()
                
                # Common dependency patterns
                if 'fix' in task_lower or 'error' in task_lower:
                    dependencies.append("analyze_codebase")
                
                if 'deploy' in task_lower or 'install' in task_lower:
                    dependencies.append("check_environment")
                
                if 'test' in task_lower:
                    dependencies.append("setup_test_environment")
                
                return json.dumps(dependencies)
            
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
            tools=[TaskAnalysisTool()]  # Add task analysis tool to executor
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
                            print(f"✅ Claimed task {task['id'][:8]}...")
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
            3. Is this the right approach?
            
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


class TaskBreakdownAgent(BaseAgent):
    """Task Breakdown Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("TaskBreakdownAgent", ["task_decomposition", "orchestration", "planning"])
        self.task_analysis_tool = TaskAnalysisTool()
    
    def get_threshold(self) -> int:
        return 6  # Moderately eager - should handle complex tasks
    
    def get_executor_instruction(self) -> str:
        return """You are a task decomposition and orchestration specialist that breaks down complex tasks.
        
        Core responsibilities:
        - Analyze complex tasks and break them into sequential, actionable steps
        - Create sub-tasks that can be handled by specialist agents
        - Manage task dependencies and orchestration
        - Prevent infinite task breakdown loops through intelligent analysis
        
        For multi-agent system tasks:
        - Break down high-level goals into concrete steps
        - Identify which specialist agents should handle each step
        - Create proper task dependency chains
        - Preserve original goal context through the breakdown
        
        Task breakdown strategy:
        1. Analyze task complexity using task_analysis tool
        2. Check available agent capabilities
        3. Break into logical sequential steps
        4. Create subtasks with proper dependencies
        5. Ensure each subtask is actionable by a specialist agent
        
        AVOID infinite breakdown:
        - Don't break down tasks that are already simple enough
        - Recognize when a task is ready for a specialist agent
        - Don't create circular dependencies
        - Stop at actionable atomic tasks
        
        Available operations: get_agent_capabilities, estimate_complexity, check_dependencies
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate complex tasks for the TaskBreakdownAgent.
        
        I can handle tasks requiring:
        - Task decomposition and planning
        - Multi-step process orchestration
        - Complex goal breakdown
        - Agent coordination planning
        
        I should handle tasks that are:
        - Too complex for individual specialist agents
        - Multi-step processes requiring coordination
        - High-level goals needing breakdown
        - Tasks requiring multiple agent types
        
        Rate task fitness (1-10) based on:
        - Task complexity (higher complexity = higher fitness)
        - Need for decomposition vs direct action
        - Multi-agent coordination requirements
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for TaskBreakdownAgent decisions.
        
        Before taking decomposition tasks, consider:
        - Is this task actually complex enough to need breakdown?
        - Would a specialist agent handle this better directly?
        - Am I creating unnecessary overhead?
        - Will breaking this down actually help achieve the goal faster?
        
        For task breakdown:
        - Are my subtasks truly actionable?
        - Do I have the right dependencies between steps?
        - Am I preserving the original goal context?
        - Will the resulting workflow be efficient?
        
        Prevent over-engineering and unnecessary complexity.
        """
    
    async def process_task(self, task_file):
        """Enhanced task processing for breakdown operations"""
        try:
            task = self.load_task(task_file)
            print(f"🔥 Processing breakdown task: {task['description']}")
            
            # Get available agent capabilities
            capabilities_result = await self.task_analysis_tool.call(
                "get_agent_capabilities", 
                workspace_path=self.workspace_path
            )
            
            # Estimate task complexity
            complexity = await self.task_analysis_tool.call(
                "estimate_complexity", 
                task_description=task['description']
            )
            
            # Check dependencies
            dependencies = await self.task_analysis_tool.call(
                "check_dependencies", 
                task_description=task['description']
            )
            
            # Enhanced breakdown prompt
            breakdown_prompt = f"""
            Task to break down: {task['description']}
            Task complexity: {complexity}/10
            Original goal: {task.get('context', {}).get('original_goal', task['description'])}
            
            Available agent capabilities:
            {capabilities_result}
            
            Potential dependencies: {dependencies}
            
            Break this task into sequential, actionable steps. For each step:
            1. Provide a clear description
            2. Specify which agent type should handle it
            3. List any dependencies on previous steps
            4. Ensure the step is atomic and actionable
            
            Return a JSON structure with:
            {{
                "breakdown_needed": true/false,
                "reasoning": "explanation of decision",
                "steps": [
                    {{
                        "description": "step description",
                        "agent_type": "AgentType",
                        "requirements": ["capability1", "capability2"],
                        "dependencies": ["step_1_id", "step_2_id"],
                        "estimated_duration": "time estimate"
                    }}
                ]
            }}
            
            If breakdown_needed is false, explain why this task should go directly to a specialist agent.
            """
            
            result = await self._run_llm_query(self.executor_runner, breakdown_prompt)
            
            # Parse the breakdown result and create subtasks
            if await self.validates_goal_progress(task, result):
                await self.create_subtasks(task, result)
                self.complete_task(task_file, result)
            else:
                self.fail_task(task_file, "Breakdown doesn't advance original goal")
                
        except Exception as e:
            print(f"❌ Error in breakdown processing: {e}")
            self.fail_task(task_file, f"Breakdown error: {str(e)}")
        finally:
            if task_file in self.active_tasks:
                self.active_tasks.remove(task_file)
    
    async def create_subtasks(self, original_task, breakdown_result):
        """Create subtasks from breakdown result"""
        try:
            # Parse the breakdown result
            import re
            json_match = re.search(r'\{.*\}', breakdown_result, re.DOTALL)
            if not json_match:
                print("❌ Could not parse breakdown result as JSON")
                return
            
            breakdown_data = json.loads(json_match.group())
            
            if not breakdown_data.get('breakdown_needed', False):
                print(f"ℹ️  Task doesn't need breakdown: {breakdown_data.get('reasoning', 'No reason provided')}")
                return
            
            steps = breakdown_data.get('steps', [])
            if not steps:
                print("❌ No steps found in breakdown")
                return
            
            print(f"🧩 Creating {len(steps)} subtasks...")
            
            # Create subtasks with proper dependencies
            subtask_ids = []
            pending_dir = os.path.join(self.workspace_path, 'tasks', 'pending')
            
            for i, step in enumerate(steps):
                subtask_id = str(uuid.uuid4())
                subtask_ids.append(subtask_id)
                
                # Map step dependencies to actual subtask IDs
                step_dependencies = []
                for dep in step.get('dependencies', []):
                    if dep.startswith('step_') and dep != f'step_{i+1}':
                        # Convert step_N to actual subtask ID
                        try:
                            dep_index = int(dep.split('_')[1]) - 1
                            if 0 <= dep_index < len(subtask_ids):
                                step_dependencies.append(subtask_ids[dep_index])
                        except (ValueError, IndexError):
                            pass
                
                subtask = {
                    "id": subtask_id,
                    "description": step['description'],
                    "type": step.get('agent_type', 'unknown').lower().replace('agent', '_operations'),
                    "requirements": step.get('requirements', []),
                    "dependencies": step_dependencies,
                    "priority": original_task.get('priority', 'medium'),
                    "context": {
                        "original_goal": original_task.get('context', {}).get('original_goal', original_task['description']),
                        "parent_task": original_task['id'],
                        "step_number": i + 1,
                        "total_steps": len(steps)
                    },
                    "created_at": datetime.utcnow().isoformat(),
                    "max_retries": 3,
                    "retry_count": 0
                }
                
                # Save subtask
                subtask_file = os.path.join(pending_dir, f"{subtask_id}.json")
                with open(subtask_file, 'w') as f:
                    json.dump(subtask, f, indent=2)
                
                print(f"   ✅ Created subtask {i+1}/{len(steps)}: {step['description'][:50]}...")
            
            print(f"🎯 Successfully created {len(steps)} subtasks for breakdown")
            
        except Exception as e:
            print(f"❌ Error creating subtasks: {e}")


# Create the main task breakdown agent for this module
task_breakdown_agent = TaskBreakdownAgent()

# Keep compatibility with ADK patterns
root_agent = task_breakdown_agent.executor 