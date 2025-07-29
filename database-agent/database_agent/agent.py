"""
Database Agent using ADK - Multi-Agent Orchestration Version

This agent provides intelligent database operations, SQL query execution, 
data management, and migration capabilities. It operates autonomously within 
a multi-agent workspace, claiming and processing database-related tasks.
"""

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import BaseTool
from typing import Dict, List, Any
import datetime
import re
import asyncio
import os
import json
import uuid
from datetime import datetime
import sqlite3
import csv

class DatabaseTool(BaseTool):
    """Custom database tool for the DatabaseAgent"""
    
    def __init__(self):
        super().__init__(
            name="database_operations",
            description="Perform database operations including queries, connections, and data management"
        )
    
    async def call(self, operation: str, query: str = None, **kwargs):
        """Execute database operations"""
        try:
            if operation == "create_connection":
                # Create a database connection
                db_type = kwargs.get('db_type', 'sqlite')
                db_path = kwargs.get('db_path', 'test.db')
                
                if db_type == 'sqlite':
                    try:
                        conn = sqlite3.connect(db_path)
                        conn.close()
                        return {
                            "success": True,
                            "db_type": db_type,
                            "db_path": db_path,
                            "message": f"SQLite database connection created: {db_path}"
                        }
                    except Exception as e:
                        return {"success": False, "error": str(e)}
                
                else:
                    return {"success": False, "error": f"Database type {db_type} not supported yet"}
            
            elif operation == "execute_query":
                # Execute SQL query
                if not query:
                    return {"success": False, "error": "SQL query required"}
                
                # Safety checks for dangerous operations
                dangerous_keywords = ['DROP TABLE', 'DELETE FROM', 'UPDATE SET', 'DROP DATABASE']
                query_upper = query.upper()
                
                if any(keyword in query_upper for keyword in dangerous_keywords):
                    safe_mode = kwargs.get('safe_mode', True)
                    if safe_mode:
                        return {
                            "success": False, 
                            "error": f"Potentially dangerous SQL operation blocked: {query}",
                            "suggestion": "Set safe_mode=False to override"
                        }
                
                db_path = kwargs.get('db_path', 'test.db')
                
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Execute query
                    cursor.execute(query)
                    
                    # Handle different query types
                    if query_upper.strip().startswith('SELECT'):
                        results = cursor.fetchall()
                        columns = [description[0] for description in cursor.description]
                        conn.close()
                        
                        return {
                            "success": True,
                            "query": query,
                            "columns": columns,
                            "rows": results,
                            "row_count": len(results)
                        }
                    
                    else:
                        # Non-SELECT queries (INSERT, UPDATE, DELETE, CREATE, etc.)
                        conn.commit()
                        affected_rows = cursor.rowcount
                        conn.close()
                        
                        return {
                            "success": True,
                            "query": query,
                            "affected_rows": affected_rows,
                            "message": "Query executed successfully"
                        }
                
                except sqlite3.Error as e:
                    return {"success": False, "error": f"SQLite error: {str(e)}"}
                except Exception as e:
                    return {"success": False, "error": f"Database error: {str(e)}"}
            
            elif operation == "list_tables":
                # List all tables in database
                db_path = kwargs.get('db_path', 'test.db')
                
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    conn.close()
                    
                    return {
                        "success": True,
                        "tables": tables,
                        "table_count": len(tables)
                    }
                
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            elif operation == "describe_table":
                # Get table schema
                table_name = kwargs.get('table_name')
                if not table_name:
                    return {"success": False, "error": "table_name required"}
                
                db_path = kwargs.get('db_path', 'test.db')
                
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    conn.close()
                    
                    schema = []
                    for col in columns:
                        schema.append({
                            "name": col[1],
                            "type": col[2],
                            "not_null": bool(col[3]),
                            "default": col[4],
                            "primary_key": bool(col[5])
                        })
                    
                    return {
                        "success": True,
                        "table_name": table_name,
                        "columns": schema,
                        "column_count": len(schema)
                    }
                
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            elif operation == "import_csv":
                # Import CSV data into table
                csv_file = kwargs.get('csv_file')
                table_name = kwargs.get('table_name')
                
                if not csv_file or not table_name:
                    return {"success": False, "error": "csv_file and table_name required"}
                
                if not os.path.exists(csv_file):
                    return {"success": False, "error": f"CSV file not found: {csv_file}"}
                
                db_path = kwargs.get('db_path', 'test.db')
                create_table = kwargs.get('create_table', True)
                
                try:
                    # Read CSV file
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        csv_reader = csv.reader(f)
                        headers = next(csv_reader)
                        rows = list(csv_reader)
                    
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Create table if requested
                    if create_table:
                        # Simple table creation - all TEXT columns
                        columns_def = ', '.join([f"{header} TEXT" for header in headers])
                        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})"
                        cursor.execute(create_sql)
                    
                    # Insert data
                    placeholders = ', '.join(['?' for _ in headers])
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(headers)}) VALUES ({placeholders})"
                    
                    cursor.executemany(insert_sql, rows)
                    conn.commit()
                    conn.close()
                    
                    return {
                        "success": True,
                        "csv_file": csv_file,
                        "table_name": table_name,
                        "rows_imported": len(rows),
                        "columns": headers
                    }
                
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            elif operation == "export_csv":
                # Export table data to CSV
                table_name = kwargs.get('table_name')
                csv_file = kwargs.get('csv_file')
                
                if not table_name or not csv_file:
                    return {"success": False, "error": "table_name and csv_file required"}
                
                db_path = kwargs.get('db_path', 'test.db')
                
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Get all data from table
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    conn.close()
                    
                    # Write to CSV
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        csv_writer = csv.writer(f)
                        csv_writer.writerow(columns)
                        csv_writer.writerows(rows)
                    
                    return {
                        "success": True,
                        "table_name": table_name,
                        "csv_file": csv_file,
                        "rows_exported": len(rows),
                        "columns": columns
                    }
                
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            elif operation == "backup_database":
                # Create database backup
                db_path = kwargs.get('db_path', 'test.db')
                backup_path = kwargs.get('backup_path')
                
                if not backup_path:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = f"{db_path}_backup_{timestamp}"
                
                try:
                    # For SQLite, we can use the backup API or simple file copy
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    
                    return {
                        "success": True,
                        "original_db": db_path,
                        "backup_path": backup_path,
                        "message": "Database backup created successfully"
                    }
                
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            elif operation == "database_info":
                # Get database information
                db_path = kwargs.get('db_path', 'test.db')
                
                if not os.path.exists(db_path):
                    return {"success": False, "error": f"Database file not found: {db_path}"}
                
                try:
                    # Get file size
                    file_size = os.path.getsize(db_path)
                    
                    # Get table count and info
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    # Get total record count
                    total_records = 0
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        total_records += count
                    
                    conn.close()
                    
                    return {
                        "success": True,
                        "db_path": db_path,
                        "file_size_bytes": file_size,
                        "table_count": len(tables),
                        "tables": tables,
                        "total_records": total_records
                    }
                
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": f"Database tool error: {str(e)}"}


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
            tools=[DatabaseTool()]  # Add database tool to executor
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
            3. Is this database operation safe to execute?
            
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


class DatabaseAgent(BaseAgent):
    """Database Agent for multi-agent orchestration system"""
    
    def __init__(self):
        super().__init__("DatabaseAgent", ["database_operations", "sql_queries", "migrations", "data_management"])
        self.database_tool = DatabaseTool()
    
    def get_threshold(self) -> int:
        return 8  # Very eager for database operations
    
    def get_executor_instruction(self) -> str:
        return """You are a database operations specialist that handles all database tasks and data management.
        
        Core responsibilities:
        - Execute SQL queries using the database_operations tool
        - Manage database connections and operations
        - Handle data imports, exports, and migrations
        - Perform database maintenance and backup operations
        
        For multi-agent system tasks:
        - Process data storage and retrieval requests
        - Handle database schema changes and migrations
        - Import/export data for other agents
        - Maintain data integrity and perform backups
        
        Database operations available:
        - create_connection: Establish database connections
        - execute_query: Run SQL queries (SELECT, INSERT, UPDATE, DELETE, CREATE)
        - list_tables: Get all tables in database
        - describe_table: Get table schema and structure
        - import_csv: Import CSV data into tables
        - export_csv: Export table data to CSV files
        - backup_database: Create database backups
        - database_info: Get database information and statistics
        
        Safety practices:
        - Always validate SQL queries before execution
        - Use safe_mode=True for potentially dangerous operations
        - Backup data before major changes
        - Verify data integrity after operations
        - Handle database connections properly
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate database and data management tasks for the DatabaseAgent.
        
        I can handle tasks requiring:
        - SQL query execution and database operations
        - Data import/export and CSV processing
        - Database schema management and migrations
        - Data backup and restoration operations
        - Database maintenance and optimization
        
        Rate task fitness (1-10) based on:
        - How well it matches database operation needs
        - Safety and complexity of database operations
        - Current workload capacity
        
        Answer YES/NO for capability and provide fitness scores.
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for DatabaseAgent decisions.
        
        Before taking database tasks, consider:
        - Is this database operation safe to execute?
        - Should I backup data before making changes?
        - Do I understand the data structure and requirements?
        - Will this operation affect data integrity?
        - Are there any concurrent operations that might conflict?
        
        For data operations:
        - Is the data format correct and validated?
        - Should I test this on a smaller dataset first?
        - Are there any foreign key constraints to consider?
        - Will this operation scale properly?
        
        Prioritize data safety and integrity above all else.
        """


# Create the main database agent for this module
database_agent = DatabaseAgent()

# Keep compatibility with ADK patterns
root_agent = database_agent.executor 