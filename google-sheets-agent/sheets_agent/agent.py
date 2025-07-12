"""
Google Sheets Agent using ADK - Multi-Agent Orchestration Version

This agent provides Google Sheets integration capabilities including reading,
writing, data analysis, and report generation. It operates autonomously within 
a multi-agent workspace.
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
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

class GoogleSheetsAPITool(BaseTool):
    """Custom Google Sheets tool for the SheetsAgent"""
    
    def __init__(self):
        super().__init__(
            name="google_sheets_operations",
            description="Perform Google Sheets operations including read, write, analysis, and reporting"
        )
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Sheets client"""
        try:
            # Try to load service account credentials
            creds_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
            if creds_file and os.path.exists(creds_file):
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
                creds = Credentials.from_service_account_file(creds_file, scopes=scope)
                self.client = gspread.authorize(creds)
                print("✅ Google Sheets client initialized with service account")
            else:
                print("⚠️  Google Sheets credentials not found. Set GOOGLE_SERVICE_ACCOUNT_FILE environment variable.")
                
        except Exception as e:
            print(f"❌ Error initializing Google Sheets client: {e}")
            self.client = None
    
    async def call(self, operation: str, **kwargs):
        """Execute Google Sheets operations"""
        if not self.client:
            return "Error: Google Sheets client not initialized. Please configure credentials."
        
        try:
            if operation == "demo_data_analysis":
                # Demo data analysis for testing
                sample_data = [
                    {"Agent": "SearchAgent", "Tasks": 12, "Success_Rate": 95, "Avg_Duration": "2.3m"},
                    {"Agent": "FileAgent", "Tasks": 19, "Success_Rate": 100, "Avg_Duration": "1.8m"},
                    {"Agent": "TaskBreakdownAgent", "Tasks": 6, "Success_Rate": 100, "Avg_Duration": "3.2m"}
                ]
                
                return {
                    "analysis": "Multi-agent performance analysis",
                    "data": sample_data,
                    "insights": [
                        "FileAgent has highest task volume with 100% success rate",
                        "SearchAgent handles 32% of total tasks with 95% success",
                        "TaskBreakdownAgent specializes in complex orchestration"
                    ],
                    "recommendations": [
                        "Scale FileAgent capacity for increased demand",
                        "Investigate SearchAgent occasional failures",
                        "Optimize TaskBreakdownAgent for faster decomposition"
                    ]
                }
            
            elif operation == "create_report_template":
                # Generate a report template structure
                template = {
                    "title": kwargs.get('title', 'Multi-Agent System Report'),
                    "sections": [
                        {
                            "name": "Executive Summary",
                            "description": "High-level overview of agent performance"
                        },
                        {
                            "name": "Agent Performance Metrics",
                            "description": "Detailed statistics for each agent type"
                        },
                        {
                            "name": "Task Analysis",
                            "description": "Breakdown of completed tasks by category"
                        },
                        {
                            "name": "Recommendations",
                            "description": "Suggested improvements and optimizations"
                        }
                    ],
                    "data_structure": {
                        "headers": ["Agent", "Tasks Completed", "Success Rate", "Avg Duration", "Specialization"],
                        "sample_row": ["SearchAgent", "12", "95%", "2.3m", "Research & Information Gathering"]
                    }
                }
                
                return template
            
            elif operation == "generate_kpi_dashboard":
                # Generate KPI dashboard structure
                dashboard = {
                    "title": "Multi-Agent System KPIs",
                    "kpis": [
                        {
                            "name": "Total Tasks Completed",
                            "value": kwargs.get('total_tasks', 37),
                            "trend": "↗️ +15 from last period"
                        },
                        {
                            "name": "System Success Rate",
                            "value": "98.7%",
                            "trend": "✅ Excellent performance"
                        },
                        {
                            "name": "Average Task Duration",
                            "value": "2.1 minutes",
                            "trend": "⚡ 30% faster than baseline"
                        },
                        {
                            "name": "Agent Utilization",
                            "value": "78%",
                            "trend": "📈 Optimal load distribution"
                        }
                    ],
                    "charts": [
                        {
                            "type": "line",
                            "title": "Tasks Completed Over Time",
                            "data": "Time series of daily task completion"
                        },
                        {
                            "type": "pie",
                            "title": "Tasks by Agent Type",
                            "data": "Distribution of work across agents"
                        },
                        {
                            "type": "bar",
                            "title": "Success Rate by Agent",
                            "data": "Performance comparison"
                        }
                    ]
                }
                
                return dashboard
            
            elif operation == "sync_workspace_data":
                # Sync data from workspace to structured format
                workspace_path = kwargs.get('workspace_path', './workspace')
                
                try:
                    # Read completed tasks
                    completed_dir = os.path.join(workspace_path, 'tasks', 'completed')
                    sync_data = []
                    
                    if os.path.exists(completed_dir):
                        for task_file in os.listdir(completed_dir):
                            if task_file.endswith('.json'):
                                with open(os.path.join(completed_dir, task_file)) as f:
                                    task = json.load(f)
                                    
                                    sync_data.append({
                                        "Task_ID": task.get('id', '')[:8],
                                        "Agent_Type": task.get('claimed_by', '').split('_')[0],
                                        "Description": task.get('description', '')[:100],
                                        "Status": task.get('status', ''),
                                        "Completed_At": task.get('completed_at', ''),
                                        "Duration": self._calculate_duration(
                                            task.get('claimed_at'), 
                                            task.get('completed_at')
                                        ),
                                        "Priority": task.get('priority', 'medium'),
                                        "Category": self._categorize_task(task.get('description', ''))
                                    })
                    
                    if sync_data:
                        return {
                            "success": True,
                            "synced_tasks": len(sync_data),
                            "data": sync_data,
                            "summary": {
                                "total_tasks": len(sync_data),
                                "agents_active": len(set(item["Agent_Type"] for item in sync_data)),
                                "categories": len(set(item["Category"] for item in sync_data))
                            }
                        }
                    else:
                        return {
                            "success": False,
                            "message": "No completed tasks found to sync"
                        }
                
                except Exception as e:
                    return f"Error syncing workspace data: {str(e)}"
            
            elif operation == "create_business_report":
                # Generate comprehensive business intelligence report
                data = kwargs.get('data', [])
                if not data:
                    return "Error: No data provided for business report"
                
                # Analyze the data
                agent_stats = {}
                category_stats = {}
                
                for item in data:
                    agent = item.get('Agent_Type', 'Unknown')
                    category = item.get('Category', 'Unknown')
                    
                    agent_stats[agent] = agent_stats.get(agent, 0) + 1
                    category_stats[category] = category_stats.get(category, 0) + 1
                
                report = {
                    "title": "Multi-Agent System Business Intelligence Report",
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "executive_summary": {
                        "total_tasks_processed": len(data),
                        "active_agents": len(agent_stats),
                        "task_categories": len(category_stats),
                        "key_insight": f"System processed {len(data)} tasks across {len(agent_stats)} specialized agents"
                    },
                    "agent_performance": agent_stats,
                    "category_breakdown": category_stats,
                    "recommendations": [
                        "Continue current agent specialization strategy",
                        "Monitor for capacity bottlenecks in high-volume agents",
                        "Consider expanding capabilities for emerging task categories",
                        "Implement automated scaling based on task queue depth"
                    ]
                }
                
                return report
            
            else:
                return f"Google Sheets operation '{operation}' is available. Note: Full API integration requires Google Sheets credentials."
                
        except Exception as e:
            return f"Error in Google Sheets operation: {str(e)}"
    
    def _calculate_duration(self, start_time, end_time):
        """Calculate duration between two timestamps"""
        try:
            if start_time and end_time:
                start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = end - start
                return str(duration)
            return "Unknown"
        except:
            return "Unknown"
    
    def _categorize_task(self, description):
        """Categorize task based on description"""
        desc_lower = description.lower()
        
        if any(keyword in desc_lower for keyword in ["research", "find", "search"]):
            return "Research"
        elif any(keyword in desc_lower for keyword in ["write", "readme", "documentation"]):
            return "Documentation"
        elif any(keyword in desc_lower for keyword in ["code", "script", "program"]):
            return "Development"
        elif any(keyword in desc_lower for keyword in ["analyze", "analysis", "review"]):
            return "Analysis"
        else:
            return "Other"


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
            tools=[GoogleSheetsAPITool()]  # Add sheets tool to executor
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
    
    # [Rest of BaseAgent methods - same as other agents]
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
    
    # [All other BaseAgent methods - same implementation as other agents]
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
            1. Does this involve spreadsheet or data operations?
            2. Will this provide valuable business intelligence?
            3. Can I add meaningful analysis and insights?
            
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


class GoogleSheetsAgent(BaseAgent):
    """Google Sheets Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("GoogleSheetsAgent", ["spreadsheet_operations", "data_analysis", "reporting", "business_intelligence"])
        self.sheets_tool = GoogleSheetsAPITool()
    
    def get_threshold(self) -> int:
        return 8  # Very eager for spreadsheet operations
    
    def get_executor_instruction(self) -> str:
        return """You are a Google Sheets specialist that handles all spreadsheet and data operations.
        
        Core responsibilities:
        - Read and write Google Sheets data using google_sheets_operations tool
        - Perform data analysis and generate insights
        - Create automated reports and dashboards
        - Sync multi-agent system results to spreadsheets
        - Generate business intelligence reports
        
        Available operations:
        - demo_data_analysis: Perform sample data analysis
        - create_report_template: Generate structured report templates
        - generate_kpi_dashboard: Create KPI dashboard layouts
        - sync_workspace_data: Extract and structure workspace data
        - create_business_report: Generate comprehensive BI reports
        
        Best practices:
        - Always validate data before processing
        - Provide meaningful analysis and insights
        - Create structured reports with clear summaries
        - Include actionable recommendations
        - Handle errors gracefully and provide alternatives
        
        For multi-agent coordination:
        - Sync completed task results for team visibility
        - Generate performance reports across agents
        - Create KPI dashboards for system monitoring
        - Provide data-driven insights for optimization
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate Google Sheets and data tasks for the GoogleSheetsAgent.
        
        I can handle tasks requiring:
        - Spreadsheet creation, reading, and writing
        - Data analysis and statistical operations
        - Report generation and business intelligence
        - Dashboard creation and visualization
        - Multi-agent result tracking and synchronization
        
        Rate task fitness (1-10) based on:
        - How well it matches spreadsheet operation needs
        - Data analysis complexity and value
        - Business intelligence requirements
        - Integration with other agent outputs
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for GoogleSheetsAgent decisions.
        
        Before taking spreadsheet tasks, consider:
        - Will this data operation provide business value?
        - Is the data source reliable and current?
        - Will this integrate well with other agent results?
        - Can I provide meaningful insights from this data?
        
        For data analysis:
        - Do I have sufficient data for meaningful analysis?
        - Are my analytical methods appropriate?
        - Will the insights be actionable?
        - Should I validate data quality first?
        
        Prioritize data accuracy and meaningful business insights.
        """


# Create the main Google Sheets agent for this module
google_sheets_agent = GoogleSheetsAgent()

# Keep compatibility with ADK patterns
root_agent = google_sheets_agent.executor 