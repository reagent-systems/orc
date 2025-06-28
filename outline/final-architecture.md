# Multi-Agent Orchestration System - Final Architecture

## Core Philosophy

**Simple agents, complex behaviors.** Individual agents monitor a shared workspace, autonomously claiming and processing tasks through file-based coordination. No central orchestrator, no direct agent communication, no complex coordination protocols.

## Fundamental Principles

### 1. Agent Independence
- Every agent runs separately (`adk web` for each)
- Agents have no knowledge of other agents
- No agent discovery, registration, or communication protocols
- Multiple instances of the same agent type can run simultaneously
- Agents can run on different machines sharing network storage

### 2. File-Based Coordination
- All coordination happens through filesystem operations
- Atomic task claiming via `os.rename()` system call
- Visual debugging - see task flow through folder structure
- No locks, no complex state management
- Works across processes and machines

### 3. Emergent Complexity
- Complex behaviors arise from simple agent interactions
- Natural selection optimizes the agent ecosystem
- Specialist agents prevent infinite task breakdown
- System self-extends by creating new agent types when needed

## Workspace Structure

```
workspace/
├── tasks/
│   ├── pending/     # Tasks waiting to be claimed
│   ├── active/      # Tasks currently being processed
│   ├── completed/   # Successfully completed tasks
│   └── failed/      # Failed tasks with error details
├── agents/          # Agent heartbeat and status files
├── context/         # Shared context from completed tasks
└── results/         # Final results and artifacts
```

## Agent Architecture

### Base Agent Class

```python
class BaseAgent:
    def __init__(self, name: str, capabilities: List[str]):
        self.name = name
        self.capabilities = capabilities
        self.workspace_path = os.getenv('WORKSPACE_PATH', './workspace')
        
        # Three-LLM Architecture
        self.executor = LLM(instruction=self.get_executor_instruction())
        self.evaluator = LLM(instruction=self.get_evaluator_instruction()) 
        self.metacognition = LLM(instruction=self.get_metacognition_instruction())
        
        # Task processing state
        self.active_tasks = []
        self.max_concurrent_tasks = self.get_max_concurrent_tasks()
        
    def get_threshold(self) -> int:
        """Return eagerness threshold (1-10). Higher = more eager to take tasks."""
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
```

### Three-LLM Architecture

Each agent uses three specialized LLMs (can be the same model endpoint):

1. **Executor LLM**: Performs the actual work
   - Processes tasks and generates results
   - Uses tools and performs actions
   - Focuses on execution efficiency

2. **Evaluator LLM**: Makes strategic decisions
   - Evaluates `can_handle()` and `should_handle()`
   - Considers workload, specialization, priority
   - Rates task fitness and agent suitability

3. **Metacognition LLM**: Provides self-reflection
   - Internal monologue about decisions
   - Prevents infinite loops and redundant work
   - Validates goal advancement

## Task Coordination

### Task Claiming Process

```python
async def monitor_workspace(self):
    """Main agent monitoring loop"""
    while True:
        pending_tasks = self.scan_pending_tasks()
        
        for task_file in pending_tasks:
            task = self.load_task(task_file)
            
            # Fast binary check
            if await self.can_handle(task):
                # Strategic decision with scoring
                if await self.should_handle(task):
                    # Atomic claim attempt
                    if self.claim_task(task_file):
                        await self.process_task(task)
                        break
        
        await asyncio.sleep(self.get_polling_interval())

def claim_task(self, task_file: str) -> bool:
    """Atomically claim a task using os.rename()"""
    active_dir = os.path.join(self.workspace_path, "tasks", "active")
    claimed_file = os.path.join(active_dir, f"{self.name}_{os.path.basename(task_file)}")
    
    try:
        os.rename(task_file, claimed_file)
        self.active_tasks.append(claimed_file)
        return True
    except OSError:
        # Another agent claimed it first
        return False
```

### Decision Functions

```python
async def can_handle(self, task) -> bool:
    """Fast binary decision based on capabilities"""
    task_requirements = task.get('requirements', [])
    
    # Check if agent has required capabilities
    if not all(req in self.capabilities for req in task_requirements):
        return False
    
    # Check current workload capacity
    if len(self.active_tasks) >= self.max_concurrent_tasks:
        return False
        
    # LLM-based capability assessment
    evaluation = await self.evaluator.process(f"""
    Task: {task}
    My capabilities: {self.capabilities}
    
    Can I handle this task? Answer YES or NO only.
    """)
    
    return evaluation.strip().upper() == "YES"

async def should_handle(self, task) -> bool:
    """Strategic decision considering priority and efficiency"""
    
    # Metacognition check for loops/redundancy
    should_consider = await self.metacognition.process(f"""
    Task: {task}
    My recent work: {self.get_recent_activity()}
    Current workload: {len(self.active_tasks)} tasks
    
    Should I consider taking this task? Consider:
    - Have I done similar work recently?
    - Will this advance the original goal?
    - Is this the best use of my capabilities?
    
    Answer YES or NO with brief reasoning.
    """)
    
    if not should_consider.strip().upper().startswith("YES"):
        return False
    
    # Strategic evaluation with scoring
    strategy_eval = await self.evaluator.process(f"""
    Task: {task}
    My threshold: {self.get_threshold()}
    Current workload: {len(self.active_tasks)}/{self.max_concurrent_tasks}
    My specializations: {self.capabilities}
    
    Rate my fitness for this task (1-10) considering:
    - How well it matches my specialization
    - Current workload capacity  
    - Task priority and urgency
    - Efficiency compared to other potential agents
    
    Provide score and reasoning.
    """)
    
    score = self.extract_score(strategy_eval)
    return score >= self.get_threshold()
```

## Loop Prevention Mechanisms

### 1. Natural Equilibrium
Specialist agents prevent infinite breakdown by claiming tasks at appropriate granularity:
- `TerminalAgent` claims "run command" tasks
- `FileAgent` claims "read file" tasks  
- `TaskBreakdownAgent` won't break down tasks other agents can handle

### 2. Semantic Deduplication
```python
async def check_task_uniqueness(self, new_task):
    """Prevent duplicate task creation using LLM semantic comparison"""
    existing_tasks = self.scan_all_tasks()
    
    for existing_task in existing_tasks:
        similarity = await self.evaluator.process(f"""
        New task: {new_task}
        Existing task: {existing_task}
        
        Are these tasks semantically equivalent? 
        Would completing one make the other unnecessary?
        
        Answer YES or NO with confidence score (1-10).
        """)
        
        if self.extract_similarity_score(similarity) > 8:
            self.log_duplicate_prevention(new_task, existing_task)
            return False
    
    return True
```

### 3. Metacognition Self-Reflection
Each agent's metacognition module provides internal monologue:
- "I just created a similar task 5 minutes ago"
- "This breakdown is getting too granular"
- "Another agent is better suited for this"

## Specific Agent Types

### TaskBreakdownAgent
```python
class TaskBreakdownAgent(BaseAgent):
    def __init__(self):
        super().__init__("TaskBreakdownAgent", ["task_decomposition", "planning"])
        
    def get_threshold(self) -> int:
        return 3  # Conservative - only breaks down truly complex tasks
        
    def get_executor_instruction(self) -> str:
        return """Break down complex tasks into smaller, actionable steps.
        
        Only break down tasks that are:
        - Too complex for a single agent
        - Require multiple different capabilities
        - Have unclear or multiple objectives
        
        Create sequential subtasks with clear dependencies.
        Each subtask should be specific and actionable.
        Avoid over-decomposition - prefer larger tasks that specialist agents can handle.
        """
```

### SearchAgent
```python
class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("SearchAgent", ["web_search", "research", "information_retrieval"])
        self.google_search_tool = GoogleSearchTool()
        
    def get_threshold(self) -> int:
        return 6  # Eager to handle search tasks
        
    def get_executor_instruction(self) -> str:
        return """Perform web searches and research using Google Search.
        
        Capabilities:
        - General web search with result summarization
        - News and current events research
        - Academic paper and documentation lookup
        - Tutorial and how-to guide discovery
        - Local business and service searches
        
        Always provide comprehensive summaries with source links.
        Focus on actionable information that advances the original goal.
        """
```

### FileAgent
```python
class FileAgent(BaseAgent):
    def __init__(self):
        super().__init__("FileAgent", ["file_operations", "code_analysis", "text_processing"])
        
    def get_threshold(self) -> int:
        return 8  # Very eager for file operations
        
    def get_executor_instruction(self) -> str:
        return """Handle all file system operations and code analysis.
        
        Capabilities:
        - Read, write, create, delete files
        - Code analysis and syntax checking
        - Text processing and content extraction
        - Directory operations and file management
        - Code refactoring and formatting
        
        Always validate file operations and provide clear feedback.
        """
```

### TerminalAgent
```python
class TerminalAgent(BaseAgent):
    def __init__(self):
        super().__init__("TerminalAgent", ["command_execution", "cli_navigation", "system_operations"])
        
    def get_threshold(self) -> int:
        return 7  # Eager for terminal operations
        
    def get_executor_instruction(self) -> str:
        return """Execute terminal commands and navigate CLI interfaces.
        
        Capabilities:
        - Shell command execution
        - Interactive CLI navigation (Firebase, AWS CLI, etc.)
        - System operations and process management
        - Package installation and environment setup
        - Git operations and version control
        
        Always explain commands before execution and capture output.
        Handle interactive prompts and menu navigation autonomously.
        """
```

## Task Processing Flow

### Task Structure
```json
{
    "id": "task_uuid",
    "description": "Human-readable task description",
    "type": "task_category",
    "requirements": ["capability1", "capability2"],
    "priority": "high|medium|low",
    "context": {
        "original_goal": "User's original objective",
        "parent_task": "parent_task_id",
        "dependencies": ["task_id1", "task_id2"]
    },
    "created_at": "2024-01-01T10:00:00Z",
    "timeout_seconds": 300,
    "max_retries": 3
}
```

### Processing Pipeline
1. **Task Discovery**: Agent scans `tasks/pending/`
2. **Capability Check**: Fast `can_handle()` evaluation
3. **Strategic Decision**: `should_handle()` with scoring
4. **Atomic Claiming**: `os.rename()` to `tasks/active/`
5. **Task Execution**: Agent processes with executor LLM
6. **Goal Validation**: Ensure result advances original objective
7. **Result Storage**: Save to `tasks/completed/` and `context/`

### Error Handling
```python
async def process_task(self, task):
    """Main task processing with error handling"""
    try:
        # Validate task hasn't expired
        if self.is_task_expired(task):
            self.fail_task(task, "Task expired")
            return
            
        # Execute the task
        result = await self.executor.process(task)
        
        # Validate result advances original goal
        if await self.validates_goal_progress(task, result):
            self.complete_task(task, result)
        else:
            self.fail_task(task, "Result doesn't advance original goal")
            
    except Exception as e:
        self.fail_task(task, f"Processing error: {str(e)}")
        
        # Retry logic
        if task.get('retry_count', 0) < task.get('max_retries', 3):
            self.schedule_retry(task)
```

## Agent Creation and Self-Extension

### Dynamic Agent Creation
When agents encounter tasks requiring missing capabilities:

```python
async def handle_missing_capability(self, task, missing_capability):
    """Create new agent type when capability is missing"""
    
    # Research the required capability
    research_task = {
        "description": f"Research how to implement {missing_capability} agent",
        "type": "research",
        "requirements": ["web_search", "research"],
        "context": {
            "agent_creation": True,
            "target_capability": missing_capability,
            "original_task": task
        }
    }
    
    # Create agent creation task
    creation_task = {
        "description": f"Create {missing_capability} agent",
        "type": "agent_creation", 
        "requirements": ["code_generation", "file_operations"],
        "context": {
            "agent_type": missing_capability,
            "capabilities": [missing_capability],
            "research_dependency": research_task["id"]
        }
    }
    
    # Drop tasks in workspace
    self.create_task(research_task)
    self.create_task(creation_task)
```

### Agent Creation Process
1. **Research Phase**: SearchAgent finds implementation patterns
2. **Code Generation**: FileAgent creates agent code
3. **Setup Phase**: TerminalAgent handles dependencies
4. **Deployment**: Agent files created in workspace
5. **Manual Startup**: User starts new agent with `adk web`

## Observability and Monitoring

### Agent Heartbeat
```python
def update_heartbeat(self):
    """Update agent status file"""
    heartbeat_file = os.path.join(self.workspace_path, "agents", f"{self.name}.json")
    
    status = {
        "agent_name": self.name,
        "capabilities": self.capabilities,
        "active_tasks": len(self.active_tasks),
        "last_heartbeat": datetime.utcnow().isoformat(),
        "status": "running"
    }
    
    with open(heartbeat_file, 'w') as f:
        json.dump(status, f, indent=2)
```

### Task Timeout Handling
```python
def check_task_timeouts(self):
    """Clean up expired tasks in active folder"""
    active_dir = os.path.join(self.workspace_path, "tasks", "active")
    
    for task_file in os.listdir(active_dir):
        if task_file.startswith(f"{self.name}_"):
            task = self.load_task(os.path.join(active_dir, task_file))
            
            if self.is_task_expired(task):
                self.fail_task(task, "Task timeout")
```

## Configuration and Deployment

### Environment Configuration
```python
# Each agent reads from environment
WORKSPACE_PATH = os.getenv('WORKSPACE_PATH', './workspace')
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '2'))
MAX_CONCURRENT_TASKS = int(os.getenv('MAX_CONCURRENT_TASKS', '3'))
MODEL_ENDPOINT = os.getenv('MODEL_ENDPOINT', 'google-ai-studio')
```

### Agent Startup
```bash
# Each agent starts independently
cd workspace/agents/search_agent && adk web --port 8001
cd workspace/agents/file_agent && adk web --port 8002  
cd workspace/agents/terminal_agent && adk web --port 8003
cd workspace/agents/breakdown_agent && adk web --port 8004
```

## System Initialization

### First-Time Setup
```python
def initialize_workspace(workspace_path: str):
    """Create initial workspace structure"""
    folders = [
        "tasks/pending",
        "tasks/active", 
        "tasks/completed",
        "tasks/failed",
        "agents",
        "context",
        "results"
    ]
    
    for folder in folders:
        os.makedirs(os.path.join(workspace_path, folder), exist_ok=True)
        
    # Create initial task from user
    initial_task = {
        "id": str(uuid.uuid4()),
        "description": input("What would you like to accomplish? "),
        "type": "user_request",
        "requirements": [],
        "priority": "medium",
        "context": {"original_goal": True},
        "created_at": datetime.utcnow().isoformat()
    }
    
    task_file = os.path.join(workspace_path, "tasks", "pending", f"{initial_task['id']}.json")
    with open(task_file, 'w') as f:
        json.dump(initial_task, f, indent=2)
```

## Key Implementation Details

### Atomic Operations
- All task claiming uses `os.rename()` - single system call
- No intermediate states or race conditions
- Visual debugging through file system state

### Polling Strategy
- Agents poll `tasks/pending/` every 1-2 seconds
- Randomized intervals prevent thundering herd
- Exponential backoff when no tasks available

### Context Flow
- Completed tasks drop results in `context/`
- Future tasks read relevant context automatically
- Semantic search for context relevance

### Memory Management
- Agents track active task count
- Automatic cleanup of expired/failed tasks
- Heartbeat files for health monitoring

## Success Metrics

### System Health Indicators
- Task completion rate
- Average task processing time
- Agent utilization rates
- Error rates and retry patterns

### Natural Optimization
- Efficient agents process more tasks
- Specialist agents prevent infinite loops
- System self-optimizes through competition

## Task Dependencies and Heartbeats

### Task Dependencies
When Task B genuinely needs Task A's results, use simple dependency chains:

```json
{
    "id": "task_deploy_123",
    "description": "Deploy application after tests pass",
    "type": "deployment",
    "requirements": ["command_execution"],
    "dependencies": ["task_test_456"],
    "status": "waiting",
    "context": {
        "original_goal": "Ship new feature",
        "parent_task": "task_parent_789"
    }
}
```

Agents check dependencies before claiming:
```python
def can_claim_task(self, task):
    dependencies = task.get('dependencies', [])
    if dependencies:
        for dep_id in dependencies:
            if not self.is_task_completed(dep_id):
                return False
    return True
```

### Task Heartbeats (Not Timeouts)
Tasks can legitimately take hours or days. Use heartbeats to show progress:

```python
def update_task_heartbeat(self, task_file):
    """Update heartbeat without timeout pressure"""
    task = self.load_task(task_file)
    task['last_heartbeat'] = datetime.utcnow().isoformat()
    task['heartbeat_count'] = task.get('heartbeat_count', 0) + 1
    
    # Save progress indicator, not timeout
    self.save_task(task_file, task)
```

## Complete Code Architecture

### Corrected Workspace Structure
```
workspace/
├── tasks/
│   ├── pending/         # New tasks awaiting pickup
│   ├── active/          # Tasks being worked on (agent_id in filename)
│   ├── completed/       # Finished tasks with results
│   ├── failed/          # Tasks that couldn't complete
│   └── waiting/         # Tasks waiting for dependencies
├── agents/              # Agent heartbeat files (no registry needed)
├── context/             # Shared context and state
└── results/             # Final deliverables
```

### Enhanced Task Format
```json
{
    "id": "task_abc123",
    "parent_id": "task_parent",
    "depth": 2,
    "type": "search_web",
    "description": "Find Python optimization techniques",
    "context": {
        "original_goal": "Optimize Python application",
        "target_domain": "performance"
    },
    "requirements": ["web_search"],
    "dependencies": ["task_xyz789"],
    "created_by": "TaskBreakdownAgent_12ab34cd",
    "created_at": "2025-01-15T10:00:00Z",
    "claimed_by": null,
    "claimed_at": null,
    "last_heartbeat": null,
    "heartbeat_count": 0,
    "max_retries": 3,
    "retry_count": 0
}
```

### Corrected Base Agent Architecture
```python
from google.adk.agents import LlmAgent
from google.adk.tools import GoogleSearchTool, FileSystemTool
import asyncio
import os
import json
import uuid
from datetime import datetime
from typing import List, Dict
import re

class BaseAgent:
    def __init__(self, agent_type: str, capabilities: List[str]):
        self.agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type
        self.capabilities = capabilities
        
        # Three-LLM architecture using proper ADK patterns
        self.executor = LlmAgent(
            name=f"{agent_type}Executor",
            model="gemini-2.0-flash",
            instruction=self.get_executor_instruction()
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
        self.workspace_path = os.getenv('WORKSPACE_PATH', 'workspace')
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
        while True:
            try:
                await self.update_heartbeat()
                
                pending_tasks = self.scan_pending_tasks()
                
                for task_file in pending_tasks:
                    task = self.load_task(task_file)
                    
                    # Check dependencies first
                    if not self.dependencies_satisfied(task):
                        continue
                    
                    if await self.should_handle(task):
                        if self.claim_task(task_file):
                            await self.process_task(task)
                            break
                
                await asyncio.sleep(self.get_polling_interval())
                
            except Exception as e:
                print(f"Error in monitor loop: {e}")
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
                return False
            
            # Capability check
            if not await self.can_handle(task):
                return False
            
            # Fitness scoring
            score = await self.calculate_fitness_score(task)
            return score >= self.get_threshold()
        
        except Exception as e:
            print(f"Error in should_handle: {e}")
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
            return "YES" in response.upper()
        
        except Exception as e:
            print(f"Error in can_handle: {e}")
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
            print(f"Error calculating fitness: {e}")
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
            print(f"Error in metacognitive check: {e}")
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
            
            # Update heartbeat periodically during processing
            self.update_task_heartbeat(task_file)
            
            # Execute the actual task
            result = await self.executor.process({
                "task": task,
                "context": self.load_relevant_context(task)
            })
            
            # Validate result advances original goal
            if await self.validates_goal_progress(task, result):
                self.complete_task(task_file, result)
            else:
                self.fail_task(task_file, "Result doesn't advance original goal")
        
        except Exception as e:
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
            print(f"Error updating heartbeat: {e}")
    
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
            print(f"Error validating goal progress: {e}")
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
            print(f"Error completing task: {e}")
    
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
            else:
                # Move to failed folder
                failed_dir = os.path.join(self.workspace_path, 'tasks', 'failed')
                os.makedirs(failed_dir, exist_ok=True)
                
                failed_file = os.path.join(failed_dir, os.path.basename(task_file))
                self.save_task(failed_file, task)
            
            # Remove from active
            os.remove(task_file)
            
        except Exception as e:
            print(f"Error failing task: {e}")
    
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
            print(f"Error updating agent heartbeat: {e}")
    
    def get_recent_actions(self) -> List[str]:
        """Get summary of recent actions for metacognition"""
        # Implementation would track recent task completions
        return []
    
    def get_workspace_summary(self) -> str:
        """Get current workspace state summary"""
        # Implementation would summarize current task counts
        return "workspace summary"
    
    def load_relevant_context(self, task) -> Dict:
        """Load relevant context for task processing"""
        # Implementation would search context folder for relevant info
        return {}
    
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
            print(f"Error saving context: {e}")
```

### Specialized Agent Types (Corrected)

```python
class TaskBreakdownAgent(BaseAgent):
    def __init__(self):
        super().__init__("TaskBreakdownAgent", ["task_decomposition", "planning"])
    
    def get_threshold(self) -> int:
        return 3  # Conservative - only handle truly complex tasks
    
    def get_executor_instruction(self) -> str:
        return """Break down complex tasks into smaller, actionable steps.
        
        Only break down tasks that are:
        - Too complex for a single agent
        - Require multiple different capabilities
        - Have unclear or multiple objectives
        
        Create sequential subtasks with clear dependencies when needed.
        Each subtask should be specific and actionable.
        Avoid over-decomposition - prefer larger tasks that specialist agents can handle.
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate if I should break down this task.
        
        I should handle tasks that are:
        - Complex multi-step processes
        - Require different types of agents
        - Have unclear decomposition
        
        I should NOT handle tasks that:
        - Are already appropriately sized
        - Other specialist agents can handle directly
        - Are too simple to break down
        """
    
    def get_metacognition_instruction(self) -> str:
        return """Reflect on task breakdown decisions.
        
        Consider:
        - Am I creating too many small tasks?
        - Would a specialist agent handle this better?
        - Is this breakdown actually helpful?
        - Have I seen similar tasks recently?
        
        Avoid creating unnecessary complexity."""
    
    async def should_handle(self, task):
        """Override to check for missing agent capabilities first"""
        try:
            # Check if we need to create a new agent type
            if await self.requires_missing_agent(task):
                await self.create_agent_creation_workflow(task)
                return False
            
            return await super().should_handle(task)
        
        except Exception as e:
            print(f"Error in TaskBreakdownAgent should_handle: {e}")
            return False
    
    async def requires_missing_agent(self, task) -> bool:
        """Check if task requires capabilities we don't have"""
        try:
            # Get current available capabilities by checking agent heartbeats
            available_capabilities = self.get_available_capabilities()
            
            prompt = f"""
            Task: {task['description']}
            Available capabilities: {available_capabilities}
            
            Does this task require capabilities that aren't available?
            Answer YES if we need a new agent type.
            """
            
            response = await self.evaluator.process(prompt)
            return "YES" in response.upper()
        
        except Exception as e:
            print(f"Error checking missing agent: {e}")
            return False
    
    def get_available_capabilities(self) -> List[str]:
        """Get capabilities from active agent heartbeats"""
        try:
            agents_dir = os.path.join(self.workspace_path, 'agents')
            if not os.path.exists(agents_dir):
                return []
            
            capabilities = []
            for file in os.listdir(agents_dir):
                if file.endswith('.json'):
                    with open(os.path.join(agents_dir, file), 'r') as f:
                        agent_data = json.load(f)
                        capabilities.extend(agent_data.get('capabilities', []))
            
            return list(set(capabilities))
        
        except Exception as e:
            print(f"Error getting capabilities: {e}")
            return []
    
    async def create_agent_creation_workflow(self, original_task):
        """Create workflow for new agent creation"""
        try:
            agent_type = await self.identify_needed_agent_type(original_task)
            
            workflow_tasks = [
                {
                    "id": str(uuid.uuid4()),
                    "description": f"Research {agent_type} implementation patterns and ADK integration",
                    "type": "research",
                    "requirements": ["web_search", "research"],
                    "context": {
                        "original_goal": original_task['description'], 
                        "agent_type": agent_type,
                        "agent_creation": True
                    },
                    "created_by": self.agent_id,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "description": f"Create {agent_type} code with proper ADK integration",
                    "type": "code_generation",
                    "requirements": ["file_operations", "code_analysis"],
                    "dependencies": [],  # Will be updated with research task ID
                    "context": {
                        "original_goal": original_task['description'], 
                        "agent_type": agent_type,
                        "agent_creation": True
                    },
                    "created_by": self.agent_id,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "description": f"Test and setup {agent_type} for deployment",
                    "type": "deployment",
                    "requirements": ["command_execution", "system_operations"],
                    "dependencies": [],  # Will be updated
                    "context": {
                        "original_goal": original_task['description'], 
                        "agent_type": agent_type,
                        "agent_creation": True
                    },
                    "created_by": self.agent_id,
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
            
            # Set up dependencies
            workflow_tasks[1]['dependencies'] = [workflow_tasks[0]['id']]
            workflow_tasks[2]['dependencies'] = [workflow_tasks[1]['id']]
            
            # Save workflow tasks
            pending_dir = os.path.join(self.workspace_path, 'tasks', 'pending')
            for task in workflow_tasks:
                task_file = os.path.join(pending_dir, f"{task['id']}.json")
                self.save_task(task_file, task)
            
            # Re-queue original task for after agent creation
            original_task['dependencies'] = [workflow_tasks[2]['id']]
            original_task['id'] = str(uuid.uuid4())  # New ID to avoid conflicts
            requeued_file = os.path.join(pending_dir, f"{original_task['id']}.json")
            self.save_task(requeued_file, original_task)
        
        except Exception as e:
            print(f"Error creating agent workflow: {e}")
    
    async def identify_needed_agent_type(self, task) -> str:
        """Identify what type of agent is needed"""
        try:
            prompt = f"""
            Task: {task['description']}
            
            What type of agent would best handle this task?
            Suggest a single, descriptive agent type name (e.g., "DatabaseAgent", "EmailAgent", "ImageProcessingAgent").
            
            Return only the agent type name.
            """
            
            response = await self.executor.process(prompt)
            return response.strip().replace(' ', '')
        
        except Exception as e:
            print(f"Error identifying agent type: {e}")
            return "CustomAgent"

class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("SearchAgent", ["web_search", "research", "information_retrieval"])
        self.search_tool = GoogleSearchTool()
    
    def get_threshold(self) -> int:
        return 6  # Eager to handle search tasks
    
    def get_executor_instruction(self) -> str:
        return """Perform web searches and research using Google Search.
        
        Capabilities:
        - General web search with result summarization
        - News and current events research
        - Academic paper and documentation lookup
        - Tutorial and how-to guide discovery
        - Local business and service searches
        
        Always provide comprehensive summaries with source links.
        Focus on actionable information that advances the original goal.
        Use the google_search tool for all searches.
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate search and research tasks.
        
        I excel at:
        - Web search queries
        - Research and information gathering
        - Finding documentation and examples
        - News and current events
        - Academic paper searches
        
        Rate tasks based on search/research requirements."""
    
    def get_metacognition_instruction(self) -> str:
        return """Reflect on search decisions.
        
        Consider:
        - Have I searched for similar information recently?
        - Will this search provide new value?
        - Is this search specific enough to be useful?
        - Does this advance the original goal?
        
        Avoid redundant searches."""

class FileAgent(BaseAgent):
    def __init__(self):
        super().__init__("FileAgent", ["file_operations", "code_analysis", "text_processing"])
        self.filesystem_tool = FileSystemTool()
    
    def get_threshold(self) -> int:
        return 8  # Very eager for file operations
    
    def get_executor_instruction(self) -> str:
        return """Handle all file system operations and code analysis.
        
        Capabilities:
        - Read, write, create, delete files
        - Code analysis and syntax checking
        - Text processing and content extraction
        - Directory operations and file management
        - Code refactoring and formatting
        - Agent code generation when needed
        
        Always validate file operations and provide clear feedback.
        Use the filesystem tool for all file operations.
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate file and code tasks.
        
        I excel at:
        - File system operations
        - Code analysis and generation
        - Text processing tasks
        - Directory management
        
        Rate tasks based on file/code requirements."""
    
    def get_metacognition_instruction(self) -> str:
        return """Reflect on file operation decisions.
        
        Consider:
        - Is this file operation safe and necessary?
        - Will this advance the goal effectively?
        - Am I duplicating existing work?
        - Should I validate before making changes?
        
        Prioritize data safety and goal advancement."""

class TerminalAgent(BaseAgent):
    def __init__(self):
        super().__init__("TerminalAgent", ["command_execution", "system_operations", "cli_navigation"])
    
    def get_threshold(self) -> int:
        return 7  # Eager for terminal operations
    
    def get_executor_instruction(self) -> str:
        return """Execute terminal commands and navigate CLI interfaces.
        
        Capabilities:
        - Shell command execution
        - Interactive CLI navigation (Firebase, AWS CLI, etc.)
        - System operations and process management
        - Package installation and environment setup
        - Git operations and version control
        - Agent deployment and testing
        
        Always explain commands before execution and capture output.
        Handle interactive prompts and menu navigation autonomously.
        """
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate terminal and system tasks.
        
        I excel at:
        - Command execution
        - System operations
        - Package management
        - Deployment tasks
        - CLI navigation
        
        Rate tasks based on terminal/system requirements."""
    
    def get_metacognition_instruction(self) -> str:
        return """Reflect on command execution decisions.
        
        Consider:
        - Is this command safe to execute?
        - Will this advance the goal?
        - Do I need elevated permissions?
        - Should I test in a safe environment first?
        
        Prioritize system safety and goal advancement."""
```

### Agent Startup (No Registry Needed)
```bash
# Start agents in separate terminals - they discover each other through heartbeats
cd search-agent && adk web --port 8001
cd file-agent && adk web --port 8002  
cd terminal-agent && adk web --port 8003
cd task-breakdown-agent && adk web --port 8004
```

## Future Extensions

### Horizontal Scaling
- Agents can run on multiple machines
- Shared network storage for workspace
- No coordination needed between machines

### Capability Evolution
- Agents learn from successful task patterns
- Automatic capability discovery
- Dynamic threshold adjustment

---

## Summary

This architecture creates a robust, scalable multi-agent system through elegant simplicity:

- **No complex coordination** - just files and atomic operations
- **Natural intelligence** - emergent behaviors from simple rules  
- **Self-extending** - system creates new agents when needed
- **Fault tolerant** - agents are independent and stateless
- **Visually debuggable** - see everything through file system
- **Horizontally scalable** - works across machines and processes

The system embodies the principle that **complex behaviors emerge from simple interactions**, creating an autonomous agent ecosystem that can tackle sophisticated tasks through decomposition and specialization. 