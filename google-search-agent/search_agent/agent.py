"""
Google Search Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent web search capabilities using Google's search API
through ADK's built-in Google Search tool. It operates autonomously within a 
multi-agent workspace, claiming and processing search-related tasks.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from typing import Dict, List
import datetime
import re
import asyncio
import os
import json
import uuid
from datetime import datetime

# Use the pre-configured Google Search tool from ADK
# This tool automatically uses environment variables for API credentials

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
            tools=[google_search]  # Add search tool to executor
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
        
        # Create runners for LLM execution
        session_service = InMemorySessionService()
        self.executor_runner = Runner(agent=self.executor, app_name=f"{agent_type}_executor", session_service=session_service)
        self.evaluator_runner = Runner(agent=self.evaluator, app_name=f"{agent_type}_evaluator", session_service=session_service)
        self.metacognition_runner = Runner(agent=self.metacognition, app_name=f"{agent_type}_metacognition", session_service=session_service)
        
        self.active_tasks = []
        # Workspace should be at project root level, shared by all agents
        self.workspace_path = os.getenv('WORKSPACE_PATH', os.path.join(os.path.dirname(__file__), '..', '..', 'workspace'))
        self.max_concurrent_tasks = int(os.getenv('MAX_CONCURRENT_TASKS', '3'))
    
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
                        claimed_file = self.claim_task(task_file)
                        if claimed_file:
                            print(f"✅ Claimed task {task['id'][:8]}...")
                            await self.process_task(claimed_file)
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
            
            response = await self._run_llm_query(self.evaluator_runner, prompt)
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
            
            response = await self._run_llm_query(self.evaluator_runner, prompt)
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
            
            response = await self._run_llm_query(self.metacognition_runner, prompt)
            return {
                'proceed': "PROCEED" in response.upper(), 
                'reasoning': response
            }
        
        except Exception as e:
            print(f"❌ Error in metacognitive check: {e}")
            return {'proceed': True, 'reasoning': 'Error in reflection'}
    
    # Atomic task claiming
    def claim_task(self, task_file: str) -> str:
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
            
            return claimed_file
        
        except (OSError, FileNotFoundError):
            # Another agent claimed it first
            return None
    
    # Task processing with goal validation
    async def process_task(self, task_file: str):
        """Process a claimed task with error handling"""
        try:
            task = self.load_task(task_file)
            print(f"🔥 Processing task: {task['description']}")
            
            # Update heartbeat periodically during processing
            self.update_task_heartbeat(task_file)
            
            # Execute the actual task
            result = await self._run_llm_query(self.executor_runner, f"""
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
            
            response = await self._run_llm_query(self.metacognition_runner, prompt)
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


class SearchAgent(BaseAgent):
    """Google Search Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("SearchAgent", ["web_search", "research", "information_retrieval"])
        self.google_search_tool = google_search
    
    def get_threshold(self) -> int:
        return 6  # Eager to handle search tasks
    
    def get_executor_instruction(self) -> str:
        return """You are a web search specialist that provides comprehensive research capabilities.
        
        Core responsibilities:
        - Perform Google web searches using the google_search tool
        - Research current information, news, and technical documentation
        - Find tutorials, guides, and implementation examples
        - Search for academic papers and scholarly content
        - Locate local businesses and services when needed
        
        For multi-agent system tasks:
        - Research ADK documentation and examples for agent creation
        - Find implementation patterns for new agent types
        - Search for tool libraries and frameworks
        - Look up best practices and coding standards
        - Find relevant technical documentation
        
        Always provide:
        - Comprehensive search results with source links
        - Summary of key findings
        - Relevance assessment for the original goal
        - Suggestions for follow-up searches if needed
        
        Use the google_search tool for all web searches.
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate search and research tasks for the SearchAgent.
        
        I can handle tasks requiring:
        - Web search and information retrieval
        - Research on technical topics
        - Finding documentation and examples
        - News and current events research
        - Academic paper searches
        - Local business searches
        
        Rate task fitness (1-10) based on:
        - How well it matches search/research needs
        - Complexity of information required
        - Current workload capacity
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for SearchAgent decisions.
        
        Before taking search tasks, consider:
        - Have I searched for similar information recently?
        - Will this search provide new value or duplicate existing work?
        - Is this search specific enough to be useful?
        - Does this advance the original goal?
        
        Prevent redundant searches and ensure meaningful contribution to multi-agent workflows.
        """


# Create the main search agent for backward compatibility
search_agent = SearchAgent()

# Keep root_agent for ADK compatibility
root_agent = search_agent.executor 