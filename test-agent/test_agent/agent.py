"""
Test Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent test execution, test generation, and quality assurance
capabilities. It operates autonomously within a multi-agent workspace, claiming and 
processing testing-related tasks.
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
import glob

class TestTool(BaseTool):
    """Custom testing tool for the TestAgent"""
    
    def __init__(self):
        super().__init__(
            name="test_operations",
            description="Perform test execution, test generation, and quality assurance operations"
        )
    
    async def call(self, operation: str, framework: str = None, **kwargs):
        """Execute testing operations"""
        try:
            if operation == "discover_tests":
                # Discover available test files and frameworks
                test_patterns = {
                    "pytest": ["test_*.py", "*_test.py", "tests/*.py"],
                    "unittest": ["test*.py", "tests/test*.py"],
                    "jest": ["*.test.js", "*.spec.js", "__tests__/**/*.js"],
                    "mocha": ["test/**/*.js", "spec/**/*.js"]
                }
                
                discovered = {}
                for fw, patterns in test_patterns.items():
                    files = []
                    for pattern in patterns:
                        files.extend(glob.glob(pattern, recursive=True))
                    if files:
                        discovered[fw] = files
                
                return {
                    "discovered_frameworks": list(discovered.keys()),
                    "test_files": discovered,
                    "total_files": sum(len(files) for files in discovered.values())
                }
            
            elif operation == "run_tests":
                # Run tests based on framework
                framework = framework or kwargs.get('framework', 'pytest')
                test_path = kwargs.get('test_path', '.')
                verbose = kwargs.get('verbose', True)
                
                if framework == "pytest":
                    cmd = ['python', '-m', 'pytest']
                    if verbose:
                        cmd.append('-v')
                    cmd.append(test_path)
                
                elif framework == "unittest":
                    cmd = ['python', '-m', 'unittest']
                    if verbose:
                        cmd.append('-v')
                    if test_path != '.':
                        cmd.append(test_path)
                    else:
                        cmd.append('discover')
                
                elif framework == "jest":
                    cmd = ['npm', 'test']
                    if verbose:
                        cmd.append('--verbose')
                
                elif framework == "mocha":
                    cmd = ['npx', 'mocha']
                    if verbose:
                        cmd.append('--reporter', 'spec')
                    cmd.append(test_path)
                
                else:
                    return f"Error: Unsupported test framework: {framework}"
                
                # Run the test command
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout for tests
                    cwd=kwargs.get('working_directory', os.getcwd())
                )
                
                return {
                    "framework": framework,
                    "command": ' '.join(cmd),
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0,
                    "test_summary": self._parse_test_output(result.stdout, framework)
                }
            
            elif operation == "generate_test":
                # Generate a basic test file
                test_type = kwargs.get('test_type', 'unit')
                target_file = kwargs.get('target_file')
                test_framework = framework or 'pytest'
                
                if not target_file:
                    return "Error: target_file required for test generation"
                
                test_content = self._generate_test_template(target_file, test_framework, test_type)
                
                return {
                    "test_content": test_content,
                    "framework": test_framework,
                    "test_type": test_type,
                    "target_file": target_file
                }
            
            elif operation == "coverage":
                # Run code coverage analysis
                framework = framework or 'pytest'
                
                if framework == "pytest":
                    # Try pytest-cov first
                    cmd = ['python', '-m', 'pytest', '--cov=.', '--cov-report=term-missing']
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode != 0:
                        # Fallback to basic coverage
                        cmd = ['python', '-m', 'coverage', 'run', '-m', 'pytest']
                        run_result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                        
                        if run_result.returncode == 0:
                            cmd = ['python', '-m', 'coverage', 'report']
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                else:
                    return f"Error: Coverage not implemented for {framework}"
                
                return {
                    "framework": framework,
                    "coverage_report": result.stdout,
                    "success": result.returncode == 0,
                    "coverage_percentage": self._extract_coverage_percentage(result.stdout)
                }
            
            elif operation == "lint":
                # Run code quality checks
                linter = kwargs.get('linter', 'auto')
                target_path = kwargs.get('target_path', '.')
                
                linters_to_try = []
                if linter == 'auto':
                    linters_to_try = ['flake8', 'pylint', 'black', 'ruff']
                else:
                    linters_to_try = [linter]
                
                results = {}
                for lint_tool in linters_to_try:
                    try:
                        if lint_tool == 'flake8':
                            cmd = ['python', '-m', 'flake8', target_path]
                        elif lint_tool == 'pylint':
                            cmd = ['python', '-m', 'pylint', target_path]
                        elif lint_tool == 'black':
                            cmd = ['python', '-m', 'black', '--check', target_path]
                        elif lint_tool == 'ruff':
                            cmd = ['ruff', 'check', target_path]
                        else:
                            continue
                        
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                        results[lint_tool] = {
                            "return_code": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "issues_found": result.returncode != 0
                        }
                    except subprocess.TimeoutExpired:
                        results[lint_tool] = {"error": "Timeout"}
                    except Exception as e:
                        results[lint_tool] = {"error": str(e)}
                
                return {
                    "linting_results": results,
                    "tools_run": list(results.keys()),
                    "issues_found": any(r.get("issues_found", False) for r in results.values())
                }
            
            elif operation == "check_dependencies":
                # Check for available testing tools
                tools_to_check = ['pytest', 'unittest', 'coverage', 'flake8', 'black', 'ruff']
                available_tools = {}
                
                for tool in tools_to_check:
                    try:
                        if tool == 'unittest':
                            # unittest is built-in
                            result = subprocess.run(['python', '-c', 'import unittest'], 
                                                  capture_output=True, timeout=10)
                        else:
                            result = subprocess.run(['python', '-m', tool, '--version'], 
                                                  capture_output=True, timeout=10)
                        
                        available_tools[tool] = {
                            "available": result.returncode == 0,
                            "version": result.stdout.strip() if result.returncode == 0 else None
                        }
                    except:
                        available_tools[tool] = {"available": False}
                
                return available_tools
            
            else:
                return f"Unknown operation: {operation}"
                
        except subprocess.TimeoutExpired:
            return f"Error: Test operation timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _parse_test_output(self, output: str, framework: str) -> Dict:
        """Parse test output to extract summary information"""
        try:
            if framework == "pytest":
                # Look for patterns like "3 passed, 1 failed"
                match = re.search(r'(\d+) passed.*?(\d+) failed', output)
                if match:
                    return {"passed": int(match.group(1)), "failed": int(match.group(2))}
                
                match = re.search(r'(\d+) passed', output)
                if match:
                    return {"passed": int(match.group(1)), "failed": 0}
            
            elif framework == "unittest":
                # Look for patterns like "Ran 5 tests in 0.001s"
                match = re.search(r'Ran (\d+) tests', output)
                if match:
                    total = int(match.group(1))
                    if "FAILED" in output:
                        # Try to count failures
                        failures = output.count("FAIL:")
                        return {"passed": total - failures, "failed": failures}
                    else:
                        return {"passed": total, "failed": 0}
            
            return {"summary": "Could not parse test results"}
        
        except Exception:
            return {"summary": "Error parsing test results"}
    
    def _generate_test_template(self, target_file: str, framework: str, test_type: str) -> str:
        """Generate a basic test template"""
        module_name = os.path.splitext(os.path.basename(target_file))[0]
        
        if framework == "pytest":
            return f'''"""
Test module for {target_file}
Generated by TestAgent
"""

import pytest
from {module_name} import *


class Test{module_name.title()}:
    """Test class for {module_name} module"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # TODO: Implement test
        assert True
    
    def test_edge_cases(self):
        """Test edge cases"""
        # TODO: Implement edge case tests
        assert True
    
    def test_error_handling(self):
        """Test error handling"""
        # TODO: Implement error handling tests
        assert True


# Integration tests
def test_integration():
    """Test integration scenarios"""
    # TODO: Implement integration tests
    assert True
'''
        
        elif framework == "unittest":
            return f'''"""
Test module for {target_file}
Generated by TestAgent
"""

import unittest
from {module_name} import *


class Test{module_name.title()}(unittest.TestCase):
    """Test class for {module_name} module"""
    
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # TODO: Implement test
        self.assertTrue(True)
    
    def test_edge_cases(self):
        """Test edge cases"""
        # TODO: Implement edge case tests
        self.assertTrue(True)
    
    def test_error_handling(self):
        """Test error handling"""
        # TODO: Implement error handling tests
        self.assertTrue(True)
    
    def tearDown(self):
        """Clean up after tests"""
        pass


if __name__ == '__main__':
    unittest.main()
'''
        
        else:
            return f"# Test template for {target_file}\n# Framework: {framework}\n# TODO: Implement tests"
    
    def _extract_coverage_percentage(self, output: str) -> str:
        """Extract coverage percentage from coverage report"""
        try:
            # Look for patterns like "TOTAL 85%"
            match = re.search(r'TOTAL.*?(\d+)%', output)
            if match:
                return f"{match.group(1)}%"
            
            # Alternative pattern
            match = re.search(r'coverage.*?(\d+)%', output, re.IGNORECASE)
            if match:
                return f"{match.group(1)}%"
            
            return "Unknown"
        except:
            return "Unknown"


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
            tools=[TestTool()]  # Add test tool to executor
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
            3. Do I have the right testing tools available?
            
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


class TestAgent(BaseAgent):
    """Test Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("TestAgent", ["test_execution", "test_generation", "quality_assurance"])
        self.test_tool = TestTool()
    
    def get_threshold(self) -> int:
        return 7  # Eager for testing operations
    
    def get_executor_instruction(self) -> str:
        return """You are a testing and quality assurance specialist that handles all testing operations.
        
        Core responsibilities:
        - Run test suites using the test_operations tool
        - Generate test files and test cases
        - Perform code quality analysis and linting
        - Execute code coverage analysis
        - Validate software quality and reliability
        
        For multi-agent system tasks:
        - Run tests for code changes made by other agents
        - Generate tests for new functionality
        - Perform quality checks before deployments
        - Validate that changes don't break existing functionality
        
        Testing operations available:
        - discover_tests: Find available test files and frameworks
        - run_tests: Execute tests with various frameworks (pytest, unittest, jest, mocha)
        - generate_test: Create test templates and basic test files
        - coverage: Analyze code coverage and identify untested areas
        - lint: Run code quality checks (flake8, pylint, black, ruff)
        - check_dependencies: Verify testing tools availability
        
        Best practices:
        - Always check for existing tests before generating new ones
        - Run tests in isolation to avoid interference
        - Provide clear test results and summaries
        - Generate meaningful test cases that cover edge cases
        - Ensure tests are maintainable and well-documented
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate testing and quality assurance tasks for the TestAgent.
        
        I can handle tasks requiring:
        - Test execution and test suite management
        - Test generation and test case creation
        - Code quality analysis and linting
        - Coverage analysis and reporting
        - Integration and unit testing
        
        Rate task fitness (1-10) based on:
        - How well it matches testing operation needs
        - Availability of required testing frameworks
        - Current workload capacity
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for TestAgent decisions.
        
        Before taking testing tasks, consider:
        - Are the required testing frameworks available?
        - Will running these tests interfere with ongoing work?
        - Should I check the current code state before testing?
        - Are there any conflicts with concurrent testing?
        - Will this testing provide meaningful feedback?
        
        For test generation:
        - Do I understand the code well enough to write good tests?
        - Are there existing tests I should build upon?
        - Should I focus on unit tests or integration tests?
        - Will these tests actually catch real issues?
        
        Prioritize test quality and meaningful coverage over quantity.
        """


# Create the main test agent for this module
test_agent = TestAgent()

# Keep compatibility with ADK patterns
root_agent = test_agent.executor 