"""
API Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent API testing, HTTP request handling, integration testing,
and webhook processing capabilities. It operates autonomously within a multi-agent 
workspace, claiming and processing API-related tasks.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool
from typing import Dict, List, Any
import datetime
import re
import asyncio
import os
import json
import uuid
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error

class APITool(BaseTool):
    """Custom API tool for the APIAgent"""
    
    def __init__(self):
        super().__init__(
            name="api_operations",
            description="Perform API testing, HTTP requests, and endpoint validation operations"
        )
    
    async def call(self, operation: str, url: str = None, **kwargs):
        """Execute API operations"""
        try:
            if operation == "http_request":
                # Make HTTP request
                if not url:
                    return {"success": False, "error": "URL required for HTTP request"}
                
                method = kwargs.get('method', 'GET').upper()
                headers = kwargs.get('headers', {})
                data = kwargs.get('data')
                timeout = kwargs.get('timeout', 30)
                
                # Prepare headers
                if isinstance(headers, dict):
                    header_items = []
                    for key, value in headers.items():
                        header_items.append((key, str(value)))
                    headers = dict(header_items)
                
                # Prepare data
                if data and isinstance(data, dict):
                    data = json.dumps(data).encode('utf-8')
                    if 'Content-Type' not in headers:
                        headers['Content-Type'] = 'application/json'
                elif data and isinstance(data, str):
                    data = data.encode('utf-8')
                
                try:
                    # Create request
                    req = urllib.request.Request(url, data=data, headers=headers, method=method)
                    
                    # Make request
                    start_time = datetime.now()
                    with urllib.request.urlopen(req, timeout=timeout) as response:
                        end_time = datetime.now()
                        
                        response_data = response.read().decode('utf-8')
                        response_headers = dict(response.headers)
                        
                        return {
                            "success": True,
                            "method": method,
                            "url": url,
                            "status_code": response.getcode(),
                            "response_headers": response_headers,
                            "response_data": response_data,
                            "response_time_ms": int((end_time - start_time).total_seconds() * 1000),
                            "content_length": len(response_data)
                        }
                
                except urllib.error.HTTPError as e:
                    error_data = e.read().decode('utf-8') if e.fp else ""
                    return {
                        "success": False,
                        "method": method,
                        "url": url,
                        "status_code": e.code,
                        "error": f"HTTP {e.code}: {e.reason}",
                        "error_data": error_data
                    }
                
                except urllib.error.URLError as e:
                    return {
                        "success": False,
                        "method": method,
                        "url": url,
                        "error": f"URL Error: {e.reason}"
                    }
                
                except Exception as e:
                    return {
                        "success": False,
                        "method": method,
                        "url": url,
                        "error": f"Request failed: {str(e)}"
                    }
            
            elif operation == "test_endpoint":
                # Test API endpoint with validation
                if not url:
                    return {"success": False, "error": "URL required for endpoint testing"}
                
                expected_status = kwargs.get('expected_status', 200)
                expected_content_type = kwargs.get('expected_content_type')
                test_data = kwargs.get('test_data')
                
                # Make request
                request_result = await self.call('http_request', url, **kwargs)
                
                if not request_result.get('success'):
                    return {
                        "success": False,
                        "test_result": "FAILED",
                        "error": "Request failed",
                        "details": request_result
                    }
                
                # Validate response
                validations = []
                test_passed = True
                
                # Status code validation
                actual_status = request_result.get('status_code')
                if actual_status == expected_status:
                    validations.append({"test": "status_code", "expected": expected_status, "actual": actual_status, "passed": True})
                else:
                    validations.append({"test": "status_code", "expected": expected_status, "actual": actual_status, "passed": False})
                    test_passed = False
                
                # Content type validation
                if expected_content_type:
                    content_type = request_result.get('response_headers', {}).get('Content-Type', '')
                    if expected_content_type.lower() in content_type.lower():
                        validations.append({"test": "content_type", "expected": expected_content_type, "actual": content_type, "passed": True})
                    else:
                        validations.append({"test": "content_type", "expected": expected_content_type, "actual": content_type, "passed": False})
                        test_passed = False
                
                # Response time validation (< 5 seconds by default)
                max_response_time = kwargs.get('max_response_time_ms', 5000)
                actual_time = request_result.get('response_time_ms', 0)
                if actual_time <= max_response_time:
                    validations.append({"test": "response_time", "expected": f"<= {max_response_time}ms", "actual": f"{actual_time}ms", "passed": True})
                else:
                    validations.append({"test": "response_time", "expected": f"<= {max_response_time}ms", "actual": f"{actual_time}ms", "passed": False})
                    test_passed = False
                
                return {
                    "success": True,
                    "test_result": "PASSED" if test_passed else "FAILED",
                    "endpoint": url,
                    "validations": validations,
                    "request_details": request_result
                }
            
            elif operation == "validate_json":
                # Validate JSON response structure
                response_data = kwargs.get('response_data')
                expected_schema = kwargs.get('expected_schema', {})
                
                if not response_data:
                    return {"success": False, "error": "response_data required for JSON validation"}
                
                try:
                    # Parse JSON if it's a string
                    if isinstance(response_data, str):
                        parsed_data = json.loads(response_data)
                    else:
                        parsed_data = response_data
                    
                    # Basic schema validation
                    validation_results = []
                    
                    # Check required fields
                    required_fields = expected_schema.get('required', [])
                    for field in required_fields:
                        if field in parsed_data:
                            validation_results.append({"field": field, "test": "required", "passed": True})
                        else:
                            validation_results.append({"field": field, "test": "required", "passed": False})
                    
                    # Check field types
                    field_types = expected_schema.get('types', {})
                    for field, expected_type in field_types.items():
                        if field in parsed_data:
                            actual_type = type(parsed_data[field]).__name__
                            if actual_type == expected_type or (expected_type == 'string' and actual_type == 'str'):
                                validation_results.append({"field": field, "test": "type", "expected": expected_type, "actual": actual_type, "passed": True})
                            else:
                                validation_results.append({"field": field, "test": "type", "expected": expected_type, "actual": actual_type, "passed": False})
                    
                    all_passed = all(result.get('passed', False) for result in validation_results)
                    
                    return {
                        "success": True,
                        "validation_result": "PASSED" if all_passed else "FAILED",
                        "parsed_data": parsed_data,
                        "validations": validation_results
                    }
                
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Invalid JSON: {str(e)}",
                        "validation_result": "FAILED"
                    }
            
            elif operation == "batch_test":
                # Test multiple endpoints
                endpoints = kwargs.get('endpoints', [])
                if not endpoints:
                    return {"success": False, "error": "endpoints list required for batch testing"}
                
                results = []
                for i, endpoint_config in enumerate(endpoints):
                    if isinstance(endpoint_config, str):
                        # Simple URL
                        test_result = await self.call('test_endpoint', endpoint_config)
                    elif isinstance(endpoint_config, dict):
                        # Full configuration
                        endpoint_url = endpoint_config.get('url')
                        test_result = await self.call('test_endpoint', endpoint_url, **endpoint_config)
                    else:
                        test_result = {"success": False, "error": f"Invalid endpoint config at index {i}"}
                    
                    results.append({
                        "index": i,
                        "endpoint": endpoint_config,
                        "result": test_result
                    })
                
                total_tests = len(results)
                passed_tests = sum(1 for r in results if r['result'].get('test_result') == 'PASSED')
                
                return {
                    "success": True,
                    "batch_result": "PASSED" if passed_tests == total_tests else "FAILED",
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": total_tests - passed_tests,
                    "test_results": results
                }
            
            elif operation == "check_url_health":
                # Quick health check for URL
                if not url:
                    return {"success": False, "error": "URL required for health check"}
                
                try:
                    start_time = datetime.now()
                    req = urllib.request.Request(url, method='HEAD')
                    with urllib.request.urlopen(req, timeout=10) as response:
                        end_time = datetime.now()
                        
                        return {
                            "success": True,
                            "url": url,
                            "status": "healthy",
                            "status_code": response.getcode(),
                            "response_time_ms": int((end_time - start_time).total_seconds() * 1000)
                        }
                
                except urllib.error.HTTPError as e:
                    return {
                        "success": True,
                        "url": url,
                        "status": "reachable_but_error",
                        "status_code": e.code,
                        "error": f"HTTP {e.code}: {e.reason}"
                    }
                
                except Exception as e:
                    return {
                        "success": False,
                        "url": url,
                        "status": "unreachable",
                        "error": str(e)
                    }
            
            elif operation == "parse_webhook":
                # Parse and validate webhook payload
                payload = kwargs.get('payload')
                webhook_type = kwargs.get('webhook_type', 'generic')
                
                if not payload:
                    return {"success": False, "error": "payload required for webhook parsing"}
                
                try:
                    # Parse JSON payload
                    if isinstance(payload, str):
                        parsed_payload = json.loads(payload)
                    else:
                        parsed_payload = payload
                    
                    # Extract common webhook fields
                    webhook_info = {
                        "webhook_type": webhook_type,
                        "payload_size": len(str(payload)),
                        "timestamp": parsed_payload.get('timestamp') or datetime.utcnow().isoformat(),
                        "event_type": parsed_payload.get('event') or parsed_payload.get('type') or parsed_payload.get('action'),
                        "source": parsed_payload.get('source') or parsed_payload.get('sender', {}).get('login'),
                        "parsed_payload": parsed_payload
                    }
                    
                    return {
                        "success": True,
                        "webhook_info": webhook_info
                    }
                
                except json.JSONDecodeError as e:
                    return {
                        "success": False,
                        "error": f"Invalid webhook JSON: {str(e)}"
                    }
            
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": f"API tool error: {str(e)}"}


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
            tools=[APITool()]  # Add API tool to executor
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
                        if self.claim_task(task_file):
                            print(f"✅ Claimed task {task['id'][:8]}...")
                            await self.process_task(task_file)
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
            3. Is this API request safe to make?
            
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


class APIAgent(BaseAgent):
    """API Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("APIAgent", ["api_testing", "http_requests", "integration_testing", "webhook_handling"])
        self.api_tool = APITool()
    
    def get_threshold(self) -> int:
        return 7  # Eager for API operations
    
    def get_executor_instruction(self) -> str:
        return """You are an API testing and HTTP operations specialist that handles all API-related tasks.
        
        Core responsibilities:
        - Perform HTTP requests using the api_operations tool
        - Test API endpoints and validate responses
        - Handle webhook processing and validation
        - Execute integration testing and batch API tests
        
        For multi-agent system tasks:
        - Test APIs for other agents and services
        - Validate API integrations and data flows
        - Process webhook notifications and events
        - Monitor API health and performance
        
        API operations available:
        - http_request: Make HTTP requests (GET, POST, PUT, DELETE, etc.)
        - test_endpoint: Test API endpoints with validation
        - validate_json: Validate JSON response structure and schema
        - batch_test: Test multiple endpoints in sequence
        - check_url_health: Quick health checks for URLs
        - parse_webhook: Parse and validate webhook payloads
        
        Best practices:
        - Always validate API responses and status codes
        - Include proper headers and authentication when needed
        - Handle timeouts and errors gracefully
        - Provide clear test results and validation reports
        - Respect rate limits and API usage guidelines
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate API testing and HTTP operation tasks for the APIAgent.
        
        I can handle tasks requiring:
        - HTTP requests and API calls
        - API endpoint testing and validation
        - Integration testing and batch operations
        - Webhook processing and event handling
        - API health monitoring and diagnostics
        
        Rate task fitness (1-10) based on:
        - How well it matches API operation needs
        - Safety and appropriateness of API requests
        - Current workload capacity
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for APIAgent decisions.
        
        Before taking API tasks, consider:
        - Is this API request safe and appropriate to make?
        - Do I have proper authentication or permissions?
        - Will this request cause any side effects or changes?
        - Should I rate-limit my requests to be respectful?
        - Is this the right time to make this API call?
        
        For API testing:
        - Are my test scenarios comprehensive but not excessive?
        - Will these tests provide meaningful validation?
        - Should I test against production or staging endpoints?
        - Am I validating the right aspects of the API response?
        
        Prioritize safety, respect for APIs, and meaningful testing.
        """


# Create the main api agent for this module
api_agent = APIAgent()

# Keep compatibility with ADK patterns
root_agent = api_agent.executor 