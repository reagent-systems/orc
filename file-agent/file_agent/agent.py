"""
File Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent file operations, code analysis, and agent generation
capabilities. It operates autonomously within a multi-agent workspace, claiming and 
processing file-related tasks.
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
import shutil
from pathlib import Path

class FileSystemTool(BaseTool):
    """Custom file system tool for the FileAgent"""
    
    def __init__(self):
        super().__init__(
            name="file_operations",
            description="Perform file system operations including read, write, create, delete files and directories"
        )
    
    async def call(self, operation: str, file_path: str = None, content: str = None, **kwargs):
        """Execute file system operations"""
        try:
            # Use file_path from kwargs if not provided directly
            path = file_path or kwargs.get('path', '')
            if not path:
                return "Error: No file path provided"
            
            # Resolve path relative to workspace directory
            workspace_path = os.getenv('WORKSPACE_PATH', os.path.join(os.path.dirname(__file__), '..', '..', 'workspace'))
            if not os.path.isabs(path):
                path = os.path.join(workspace_path, path)
            
            if operation == "read":
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif operation == "write":
                # Ensure directory exists
                dir_path = os.path.dirname(path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content or '')
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
        """Process a claimed task with error handling and tool execution"""
        try:
            task = self.load_task(task_file)
            print(f"🔥 Processing task: {task['description']}")
            
            # Update heartbeat periodically during processing
            self.update_task_heartbeat(task_file)
            
            # Step 1: Generate execution plan
            plan = await self._run_llm_query(self.executor_runner, f"""
            Task to execute: {task['description']}
            Task type: {task.get('type', 'unknown')}
            Context: {task.get('context', {})}
            
            Generate a detailed execution plan using the file_operations tool.
            The plan should include specific file operations to complete this task.
            Return the plan as a structured response.
            """)
            
            print(f"📋 Generated plan: {plan[:100]}...")
            
            # Step 2: Execute the plan using tools
            execution_result = await self._execute_plan_with_tools(task, plan)
            
            # Step 3: Validate result advances original goal
            if await self.validates_goal_progress(task, execution_result):
                print(f"✅ Task completed successfully")
                self.complete_task(task_file, execution_result)
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
    
    async def _execute_plan_with_tools(self, task, plan):
        """Execute the plan using actual tools"""
        try:
            print(f"🔧 Executing plan with tools...")
            print(f"📋 Plan: {plan[:200]}...")
            
            # Parse the plan to extract tool calls
            tool_calls = self._extract_tool_calls(plan)
            print(f"🔍 Extracted {len(tool_calls)} tool calls: {tool_calls}")
            
            if not tool_calls:
                print(f"⚠️ No tool calls found in plan, returning plan as result")
                return f"Plan generated but no tools executed:\n{plan}"
            
            results = []
            for i, tool_call in enumerate(tool_calls):
                print(f"🔧 Executing tool call {i+1}/{len(tool_calls)}: {tool_call['operation']}")
                
                try:
                    # Execute the tool call
                    print(f"🔧 Calling tool: {tool_call['operation']} with path='{tool_call.get('path', '')}' content='{tool_call.get('content', '')[:50]}...'")
                    result = await self.filesystem_tool.call(
                        operation=tool_call['operation'],
                        path=tool_call.get('path', ''),
                        content=tool_call.get('content', ''),
                        **tool_call.get('kwargs', {})
                    )
                    
                    results.append({
                        'tool_call': tool_call,
                        'result': result,
                        'success': True
                    })
                    
                    print(f"✅ Tool execution successful: {result[:50]}...")
                    
                except Exception as e:
                    results.append({
                        'tool_call': tool_call,
                        'result': f"Error: {str(e)}",
                        'success': False
                    })
                    print(f"❌ Tool execution failed: {e}")
            
            # Compile final result
            execution_summary = {
                'task_description': task['description'],
                'plan': plan,
                'tool_executions': results,
                'successful_executions': len([r for r in results if r['success']]),
                'total_executions': len(results)
            }
            
            return f"Task execution completed:\n{execution_summary}"
            
        except Exception as e:
            print(f"❌ Error executing plan: {e}")
            return f"Error executing plan: {str(e)}\nOriginal plan: {plan}"
    
    def _extract_tool_calls(self, plan):
        """Extract tool calls from the LLM-generated plan"""
        tool_calls = []
        
        try:
            # Look for file_operations calls in the plan
            lines = plan.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Handle code block format: ```tool_code\nfile_operations.write(...)
                if '```tool_code' in line:
                    # Extract the tool call from the code block
                    tool_call_start = line.find('file_operations.')
                    if tool_call_start != -1:
                        tool_call_text = line[tool_call_start:]
                        # Remove trailing ```
                        if tool_call_text.endswith('```'):
                            tool_call_text = tool_call_text[:-3]
                        
                        # Parse the tool call
                        if 'file_operations.write' in tool_call_text:
                            try:
                                # Extract parameters from file_operations.write(file_path='test.txt', content='This is a test file')
                                if 'file_path=' in tool_call_text and 'content=' in tool_call_text:
                                    path_start = tool_call_text.find("file_path='") + 11
                                    path_end = tool_call_text.find("'", path_start)
                                    path = tool_call_text[path_start:path_end]
                                    
                                    content_start = tool_call_text.find("content='") + 9
                                    content_end = tool_call_text.find("'", content_start)
                                    content = tool_call_text[content_start:content_end]
                                    
                                    tool_calls.append({
                                        'operation': 'write',
                                        'path': path,
                                        'content': content,
                                        'kwargs': {}
                                    })
                            except:
                                pass
                
                # Look for file_operations.write calls with different formats
                elif 'file_operations.write' in line:
                    # Format 1: file_operations.write(file_path="hello.py", file_content="print('hello world')")
                    if 'file_path=' in line and 'file_content=' in line:
                        try:
                            path_start = line.find('file_path="') + 11
                            path_end = line.find('"', path_start)
                            path = line[path_start:path_end]
                            
                            content_start = line.find('file_content="') + 14
                            content_end = line.find('"', content_start)
                            content = line[content_start:content_end]
                            
                            tool_calls.append({
                                'operation': 'write',
                                'path': path,
                                'content': content,
                                'kwargs': {}
                            })
                        except:
                            pass
                    
                    # Format 2: file_operations.write(filename="hello.py", content="print('hello world')")
                    elif 'filename=' in line and 'content=' in line:
                        try:
                            path_start = line.find('filename="') + 10
                            path_end = line.find('"', path_start)
                            path = line[path_start:path_end]
                            
                            content_start = line.find('content="') + 9
                            content_end = line.find('"', content_start)
                            content = line[content_start:content_end]
                            
                            tool_calls.append({
                                'operation': 'write',
                                'path': path,
                                'content': content,
                                'kwargs': {}
                            })
                        except:
                            pass
                
                # Look for file_operations.read calls
                elif 'file_operations.read' in line:
                    # Format 1: file_operations.read(file_path="hello.py")
                    if 'file_path=' in line:
                        try:
                            path_start = line.find('file_path="') + 11
                            path_end = line.find('"', path_start)
                            path = line[path_start:path_end]
                            
                            tool_calls.append({
                                'operation': 'read',
                                'path': path,
                                'kwargs': {}
                            })
                        except:
                            pass
                    
                    # Format 2: file_operations.read(filename="hello.py")
                    elif 'filename=' in line:
                        try:
                            path_start = line.find('filename="') + 10
                            path_end = line.find('"', path_start)
                            path = line[path_start:path_end]
                            
                            tool_calls.append({
                                'operation': 'read',
                                'path': path,
                                'kwargs': {}
                            })
                        except:
                            pass
                
                # Look for file_operations.list calls
                elif 'file_operations.list' in line:
                    if 'path=' in line:
                        try:
                            path_start = line.find('path="') + 6
                            path_end = line.find('"', path_start)
                            path = line[path_start:path_end]
                            
                            tool_calls.append({
                                'operation': 'list',
                                'path': path,
                                'kwargs': {}
                            })
                        except:
                            pass
            
            # If no structured calls found, try to infer from the task description
            if not tool_calls:
                task_lower = plan.lower()
                if 'hello world' in task_lower and 'python' in task_lower:
                    # Create a hello world script
                    tool_calls.append({
                        'operation': 'write',
                        'path': 'hello_world.py',
                        'content': 'print("Hello, world!")',
                        'kwargs': {}
                    })
                elif 'create' in task_lower and 'file' in task_lower:
                    # Generic file creation
                    tool_calls.append({
                        'operation': 'write',
                        'path': 'created_file.txt',
                        'content': f'File created for task: {task_lower}',
                        'kwargs': {}
                    })
                elif 'python' in task_lower and 'script' in task_lower:
                    # Create a Python script
                    tool_calls.append({
                        'operation': 'write',
                        'path': 'script.py',
                        'content': 'print("Hello from Python!")',
                        'kwargs': {}
                    })
                
                # Try to extract from JSON plan format
                if 'execution_plan' in plan and 'file_path' in plan:
                    try:
                        import json
                        # Find the JSON part of the plan (handle code blocks)
                        json_start = plan.find('{')
                        json_end = plan.rfind('}') + 1
                        if json_start != -1 and json_end != -1:
                            json_str = plan[json_start:json_end]
                            # Clean up the JSON string
                            json_str = json_str.replace('\\"', '"').replace('\\n', '\n')
                            plan_data = json.loads(json_str)
                            
                            if 'execution_plan' in plan_data:
                                for step in plan_data['execution_plan']:
                                    operation = step.get('operation', 'write')
                                    file_path = step.get('file_path', '')
                                    content = step.get('content', '')
                                    
                                    if file_path and operation == 'write':
                                        tool_calls.append({
                                            'operation': 'write',
                                            'path': file_path,
                                            'content': content,
                                            'kwargs': {}
                                        })
                                    elif file_path and operation == 'read':
                                        tool_calls.append({
                                            'operation': 'read',
                                            'path': file_path,
                                            'kwargs': {}
                                        })
                    except Exception as e:
                        print(f"❌ Error parsing JSON plan: {e}")
                        # Fallback: try to extract file_path and content directly from the plan
                        # Clear any previous tool calls that might be incorrect
                        tool_calls = []
                        try:
                            if 'file_path' in plan and 'content' in plan:
                                # Extract file_path - handle escaped quotes
                                path_pattern = '"file_path": "'
                                path_start = plan.find(path_pattern) + len(path_pattern)
                                if path_start >= len(path_pattern):
                                    path_end = plan.find('"', path_start)
                                    file_path = plan[path_start:path_end]
                                    
                                    # Extract content - handle escaped quotes
                                    content_pattern = '"content": "'
                                    content_start = plan.find(content_pattern) + len(content_pattern)
                                    if content_start >= len(content_pattern):
                                        # Find the end of the content, handling escaped quotes
                                        content_end = content_start
                                        while content_end < len(plan):
                                            if plan[content_end] == '"' and plan[content_end-1] != '\\':
                                                break
                                            content_end += 1
                                        content = plan[content_start:content_end]
                                        
                                        # Clean up escaped characters
                                        content = content.replace('\\"', '"').replace('\\n', '\n')
                                        
                                        if file_path and content:
                                            tool_calls.append({
                                                'operation': 'write',
                                                'path': file_path,
                                                'content': content,
                                                'kwargs': {}
                                            })
                                            print(f"✅ Fallback extraction: {file_path} -> {content[:50]}...")
                        except Exception as e2:
                            print(f"❌ Error in fallback extraction: {e2}")
            
        except Exception as e:
            print(f"❌ Error extracting tool calls: {e}")
        
        return tool_calls
    
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