# Multi-Agent Orchestration System (ORC) - Complete Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Agent Types](#agent-types)
5. [Setup & Installation](#setup--installation)
6. [Usage Guide](#usage-guide)
7. [Task Management](#task-management)
8. [Monitoring & Debugging](#monitoring--debugging)
9. [Advanced Features](#advanced-features)
10. [Troubleshooting](#troubleshooting)
11. [API Reference](#api-reference)
12. [Contributing](#contributing)

---

## System Overview

The ORC (Orchestration) system is a **peer-to-peer multi-agent architecture** built with Google's Agent Development Kit (ADK). It enables multiple AI agents to work together autonomously to accomplish complex tasks through intelligent task decomposition and coordination.

### Key Features

- **Autonomous Operation**: Agents decide independently what tasks to take
- **Natural Equilibrium**: Specialist agents prevent infinite task breakdown loops
- **LLM-Based Intelligence**: Each agent uses three LLMs for execution, evaluation, and metacognition
- **Atomic Coordination**: Race-condition-free task claiming using `os.rename()`
- **Goal Preservation**: Original objectives are maintained through task decomposition chains
- **Self-Extending**: System can create new agents when needed capabilities are missing

### Core Philosophy

The system operates on the principle of **emergent complexity** - simple agent interactions create sophisticated workflows without central orchestration. Each agent is a specialist that:

1. **Monitors** the shared workspace for tasks
2. **Evaluates** task fitness using LLM-based decision making
3. **Claims** tasks atomically when suitable
4. **Processes** tasks with metacognitive oversight
5. **Validates** results advance the original goal

---

## Architecture

### Three-LLM Agent Architecture

Each agent contains three specialized LLMs:

```python
class BaseAgent:
    def __init__(self, agent_type: str, capabilities: List[str]):
        # Executor LLM - Performs the actual task work
        self.executor = LlmAgent(
            name=f"{agent_type}Executor",
            model="gemini-2.0-flash",
            instruction=self.get_executor_instruction()
        )
        
        # Evaluator LLM - Assesses task fitness and capability matching
        self.evaluator = LlmAgent(
            name=f"{agent_type}Evaluator", 
            model="gemini-2.0-flash",
            instruction=self.get_evaluator_instruction()
        )
        
        # Metacognition LLM - Provides self-reflection and prevents infinite loops
        self.metacognition = LlmAgent(
            name=f"{agent_type}Metacognition",
            model="gemini-2.0-flash", 
            instruction=self.get_metacognition_instruction()
        )
```

### Workspace Structure

```
workspace/
├── tasks/
│   ├── pending/     # New tasks waiting to be claimed
│   ├── active/      # Tasks currently being processed (agent_id prefix)
│   ├── completed/   # Successfully completed tasks with results
│   └── failed/      # Failed tasks with retry logic
├── agents/          # Agent heartbeat/status files
├── context/         # Task results for future reference
└── results/         # Final outputs and artifacts
```

### Task Flow

1. **Task Creation**: User drops JSON task files in `workspace/tasks/pending/`
2. **Agent Monitoring**: All agents continuously scan for new tasks
3. **Capability Evaluation**: Agents assess if they can handle each task
4. **Atomic Claiming**: First suitable agent atomically claims task via `os.rename()`
5. **Task Processing**: Agent processes task with metacognitive oversight
6. **Result Storage**: Completed tasks moved to appropriate folder with results
7. **Context Preservation**: Results saved for future task context

### Task Decomposition Flow

```
Complex Task → TaskBreakdownAgent → Subtasks → Specialist Agents → Results
```

---

## Core Components

### BaseAgent Class

The foundation for all agents in the system:

```python
class BaseAgent:
    def __init__(self, agent_type: str, capabilities: List[str], tools: List = None):
        self.agent_id = f"{agent_type}_{uuid.uuid4().hex[:8]}"
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.active_tasks = []
        self.workspace_path = os.getenv('WORKSPACE_PATH', './workspace')
        self.max_concurrent_tasks = int(os.getenv('MAX_CONCURRENT_TASKS', '3'))
```

#### Key Methods

- `monitor_workspace()`: Main agent loop
- `should_handle(task)`: LLM-based decision making
- `claim_task(task_file)`: Atomic task claiming
- `process_task(task_file)`: Task execution with validation
- `update_heartbeat()`: Agent status reporting

### Task Format

Tasks are JSON files with the following structure:

```json
{
  "id": "unique-uuid",
  "description": "Research Python web frameworks and create comparison document",
  "type": "complex_goal",
  "requirements": ["task_decomposition", "orchestration"],
  "priority": "high",
  "context": {
    "original_goal": "Learn about web frameworks",
    "deadline": "2024-01-15"
  },
  "dependencies": ["task_abc123", "task_def456"],
  "created_at": "2024-01-01T10:00:00Z",
  "max_retries": 3,
  "retry_count": 0
}
```

### Decision Making Process

Each agent uses a three-step decision process:

1. **Metacognitive Reflection**: Internal reflection on whether to take the task
2. **Capability Check**: Binary assessment of technical ability
3. **Fitness Scoring**: Numerical rating (1-10) of task suitability

```python
async def should_handle(self, task) -> bool:
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
```

---

## Agent Types

### Priority 1 Agents (Core System)

#### TaskBreakdownAgent 🧩

**Purpose**: Decomposes complex tasks into actionable sequential steps

**Capabilities**: `task_decomposition`, `orchestration`, `planning`

**Key Features**:
- Analyzes task complexity before breakdown
- Creates subtasks with proper dependencies
- Prevents infinite breakdown loops through intelligence
- Preserves original goal context throughout decomposition

**Threshold**: 6 (moderately eager - handles complex tasks)

**Special Tools**:
- `TaskAnalysisTool`: Analyzes tasks and estimates complexity
- `get_agent_capabilities`: Discovers available agent capabilities
- `estimate_complexity`: Rates task complexity (1-10)
- `check_dependencies`: Identifies implicit dependencies

#### SearchAgent 🔍

**Purpose**: Handles all web search and research operations

**Capabilities**: `web_search`, `google_search`, `research`

**Key Features**:
- Multiple search types (general, news, academic, tutorials, local)
- Result analysis and summarization
- Research task coordination

**Threshold**: 6

#### FileAgent 📁

**Purpose**: Manages all file operations and code generation

**Capabilities**: `file_operations`, `code_analysis`, `text_processing`, `agent_generation`

**Key Features**:
- Complete file operations (read, write, create, delete, copy)
- Code analysis and syntax checking
- New agent code generation
- Text processing and document creation

**Special Tools**:
- `FileSystemTool`: Comprehensive file system operations
- Agent template generation
- Code analysis and validation

#### TerminalAgent ⚡

**Purpose**: Executes system commands and manages environments

**Capabilities**: `command_execution`, `system_operations`, `cli_navigation`

**Key Features**:
- Safe command execution with built-in safety checks
- System information gathering
- Environment setup and package installation
- Process management and monitoring

**Safety Features**:
- Command validation before execution
- Dangerous command blocking
- Timeout protection
- Error handling and recovery

### Priority 2 Agents (Ready for Implementation)

#### GitAgent 🔄
- **Capabilities**: `version_control`, `code_review`, `branch_management`
- **Purpose**: Git operations and code version management

#### TestAgent 🧪
- **Capabilities**: `testing`, `validation`, `quality_assurance`
- **Purpose**: Automated testing and code validation

#### DatabaseAgent 🗄️
- **Capabilities**: `database_operations`, `query_optimization`, `schema_management`
- **Purpose**: Database operations and data management

#### APIAgent 🌐
- **Capabilities**: `api_integration`, `http_requests`, `api_testing`
- **Purpose**: API interactions and external service integration

### Priority 3 Agents (Future Development)

#### EmailAgent 📧
- **Capabilities**: `email_processing`, `communication`, `notification`
- **Purpose**: Email handling and communication

#### SlackAgent 💬
- **Capabilities**: `messaging`, `team_communication`, `notification`
- **Purpose**: Team communication and notifications

#### DataAnalysisAgent 📊
- **Capabilities**: `data_analysis`, `visualization`, `statistics`
- **Purpose**: Data analysis and insights generation

#### DocumentAgent 📄
- **Capabilities**: `document_processing`, `format_conversion`, `content_analysis`
- **Purpose**: Document handling and processing

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- Google API Key (Gemini) or Vertex AI access
- ADK installed (`pip install google-adk`)

### Quick Setup

1. **Clone and Setup Environment**:
   ```bash
   git clone <repository>
   cd orc
   python3 setup_multi_agent.py
   ```

2. **Configure Environment**:
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your API keys
   nano .env
   ```

3. **Environment Variables**:
   ```bash
   # Required: Google API access
   GOOGLE_API_KEY=your_api_key_here
   # OR for Vertex AI:
   GOOGLE_GENAI_USE_VERTEXAI=true
   
   # Optional: System tuning
   WORKSPACE_PATH=./workspace
   MAX_CONCURRENT_TASKS=3
   POLLING_INTERVAL=2
   ```

### Manual Setup

1. **Create Workspace Structure**:
   ```bash
   mkdir -p workspace/{tasks/{pending,active,completed,failed},agents,context,results}
   ```

2. **Install Dependencies**:
   ```bash
   pip install google-adk python-dotenv
   ```

3. **Test Individual Agents**:
   ```bash
   # Test SearchAgent
   cd google-search-agent
   python3 create_test_task.py
   python3 run_autonomous.py
   ```

### Starting the System

Start agents in separate terminals:

```bash
# Terminal 1 - Task Breakdown
cd task-breakdown-agent
python3 run_autonomous.py

# Terminal 2 - Search Operations  
cd google-search-agent
python3 run_autonomous.py

# Terminal 3 - File Operations
cd file-agent
python3 run_autonomous.py

# Terminal 4 - Terminal Operations
cd terminal-agent
python3 run_autonomous.py
```

---

## Usage Guide

### Creating Tasks

Tasks are JSON files placed in `workspace/tasks/pending/`. Example:

```json
{
  "id": "unique-uuid",
  "description": "Research Python web frameworks and create comparison document",
  "type": "complex_goal",
  "requirements": ["task_decomposition", "orchestration"],
  "priority": "high",
  "context": {
    "original_goal": "Learn about web frameworks",
    "deadline": "2024-01-15"
  },
  "created_at": "2024-01-01T10:00:00Z",
  "max_retries": 3
}
```

### Task Types

- `complex_goal`: Multi-step tasks requiring breakdown
- `web_search`: Search and research tasks
- `file_operations`: File system and code tasks
- `terminal_operations`: Command execution tasks
- `agent_creation`: Tasks requiring new agent development

### Example Workflows

#### 1. Complex Research Project

```bash
# Create a complex research task
echo '{
  "id": "research_web_frameworks",
  "description": "Research modern Python web frameworks, compare performance, and create a comprehensive guide",
  "type": "complex_goal",
  "requirements": ["task_decomposition", "orchestration"],
  "priority": "high",
  "context": {
    "original_goal": "Create web framework comparison guide",
    "target_audience": "developers"
  }
}' > workspace/tasks/pending/research_web_frameworks.json
```

#### 2. Code Generation Task

```bash
# Create a file operation task
echo '{
  "id": "create_api_client",
  "description": "Create a Python API client for the GitHub REST API with authentication and error handling",
  "type": "file_operations",
  "requirements": ["file_operations", "code_analysis"],
  "priority": "medium",
  "context": {
    "original_goal": "Build GitHub API integration",
    "requirements": ["authentication", "error_handling", "documentation"]
  }
}' > workspace/tasks/pending/create_api_client.json
```

#### 3. System Setup Task

```bash
# Create a terminal operation task
echo '{
  "id": "setup_development_env",
  "description": "Set up a Python development environment with virtual environment, install dependencies, and configure linting",
  "type": "terminal_operations",
  "requirements": ["command_execution", "system_operations"],
  "priority": "high",
  "context": {
    "original_goal": "Prepare development environment",
    "project_type": "Python web application"
  }
}' > workspace/tasks/pending/setup_development_env.json
```

### Testing the System

Create test tasks to see the agents in action:

```bash
# Create complex tasks for breakdown
cd task-breakdown-agent
python3 create_test_task.py

# Create file operation tasks
cd file-agent  
python3 create_test_task.py

# Create search tasks
cd google-search-agent
python3 create_test_task.py

# Create terminal tasks
cd terminal-agent
python3 create_test_task.py
```

---

## Task Management

### Task Lifecycle

1. **Pending**: Task waiting to be claimed by an agent
2. **Active**: Task being processed by an agent (prefixed with agent ID)
3. **Completed**: Task finished successfully with results
4. **Failed**: Task failed with error details and retry logic

### Task Dependencies

Tasks can specify dependencies on other tasks:

```json
{
  "id": "analyze_results",
  "description": "Analyze the research results and create insights",
  "dependencies": ["research_web_frameworks", "performance_testing"],
  "type": "file_operations"
}
```

### Retry Logic

Failed tasks automatically retry with exponential backoff:

```json
{
  "id": "failed_task",
  "status": "failed",
  "retry_count": 1,
  "max_retries": 3,
  "error": "Network timeout during search operation"
}
```

### Task Context Preservation

Results are saved to context for future tasks:

```json
{
  "task_id": "research_web_frameworks",
  "description": "Research modern Python web frameworks",
  "result": "Comprehensive analysis of Django, Flask, and FastAPI...",
  "created_at": "2024-01-01T10:00:00Z",
  "original_goal": "Create web framework comparison guide"
}
```

---

## Monitoring & Debugging

### Agent Status

Check `workspace/agents/` for agent heartbeat files:

```json
{
  "agent_id": "SearchAgent_12ab34cd",
  "agent_type": "SearchAgent",
  "capabilities": ["web_search", "google_search", "research"],
  "active_tasks": 1,
  "last_heartbeat": "2024-01-01T10:00:00Z",
  "status": "running"
}
```

### Task Progress Monitoring

Monitor task folders for progress:

- `pending/`: Tasks waiting to be claimed
- `active/`: Tasks being processed (prefixed with agent ID)
- `completed/`: Finished tasks with results
- `failed/`: Failed tasks with error details

### Logging and Debugging

Enable detailed logging by setting environment variables:

```bash
export LOG_LEVEL=DEBUG
export AGENT_DEBUG=true
```

### Common Monitoring Commands

```bash
# Check agent status
ls -la workspace/agents/

# Monitor pending tasks
ls -la workspace/tasks/pending/

# Check active tasks
ls -la workspace/tasks/active/

# View completed results
ls -la workspace/tasks/completed/

# Check failed tasks
ls -la workspace/tasks/failed/
```

### Performance Metrics

Track system performance:

- **Task completion rate**: Successful vs failed tasks
- **Agent utilization**: Active tasks per agent
- **Response time**: Time from task creation to completion
- **Breakdown efficiency**: Tasks broken down vs direct completion

---

## Advanced Features

### Self-Extension Capability

The system can create new agents when encountering tasks requiring missing capabilities:

1. **Detection**: TaskBreakdownAgent identifies missing capabilities
2. **Research**: SearchAgent researches implementation patterns
3. **Generation**: FileAgent creates new agent code
4. **Deployment**: TerminalAgent deploys and registers new agent
5. **Retry**: Original task retried with new capabilities

### Metacognitive Oversight

Each agent includes metacognitive reflection to prevent:

- **Infinite loops**: Agents recognize when they're creating redundant work
- **Goal drift**: Results are validated against original objectives
- **Over-engineering**: Agents step back when simpler solutions exist
- **Resource waste**: Agents avoid unnecessary task breakdown

### Atomic Coordination

Race-condition-free task claiming using `os.rename()`:

```python
def claim_task(self, task_file: str) -> str:
    try:
        active_dir = os.path.join(self.workspace_path, 'tasks', 'active')
        os.makedirs(active_dir, exist_ok=True)
        
        task_name = os.path.basename(task_file)
        claimed_file = os.path.join(active_dir, f"{self.agent_id}_{task_name}")
        
        # Atomic operation
        os.rename(task_file, claimed_file)
        return claimed_file
    except (OSError, FileNotFoundError):
        # Another agent claimed it first
        return None
```

### Goal Validation

Results are validated against original goals:

```python
async def validates_goal_progress(self, task, result) -> bool:
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
```

### Custom Tools Integration

Agents can use custom tools for specialized capabilities:

```python
class CustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="custom_operation",
            description="Custom tool description"
        )
    
    async def call(self, operation: str, **kwargs):
        # Custom tool implementation
        pass
```

---

## Troubleshooting

### Common Issues

#### 1. Agents Not Starting

**Symptoms**: Agents fail to start or show connection errors

**Solutions**:
- Check API key configuration in `.env`
- Verify ADK installation: `pip install google-adk`
- Check network connectivity
- Validate workspace directory permissions

#### 2. Tasks Not Being Claimed

**Symptoms**: Tasks remain in pending folder indefinitely

**Solutions**:
- Check agent capabilities match task requirements
- Verify agent thresholds are appropriate
- Check for dependency issues
- Review agent heartbeat files

#### 3. Infinite Task Breakdown

**Symptoms**: Tasks keep getting broken down without completion

**Solutions**:
- Check metacognitive reflection logic
- Verify specialist agents are running
- Review task complexity thresholds
- Check for circular dependencies

#### 4. Failed Tasks Not Retrying

**Symptoms**: Failed tasks don't move back to pending

**Solutions**:
- Check retry count vs max_retries
- Verify error handling in task processing
- Review file permissions for task movement
- Check for exception handling issues

### Debug Commands

```bash
# Check agent heartbeats
find workspace/agents/ -name "*.json" -exec cat {} \;

# Monitor task movement
watch -n 1 'ls -la workspace/tasks/*/'

# Check for stuck tasks
find workspace/tasks/active/ -mmin +30 -name "*.json"

# Validate task JSON format
python3 -m json.tool workspace/tasks/pending/task.json
```

### Performance Optimization

#### 1. Reduce Polling Frequency

```bash
export POLLING_INTERVAL=5  # Default is 2 seconds
```

#### 2. Limit Concurrent Tasks

```bash
export MAX_CONCURRENT_TASKS=2  # Default is 3
```

#### 3. Optimize LLM Usage

- Use appropriate model sizes for different LLM roles
- Implement caching for repeated queries
- Batch similar operations

---

## API Reference

### BaseAgent Methods

#### Core Methods

```python
async def monitor_workspace(self):
    """Main agent monitoring loop"""
    pass

async def should_handle(self, task) -> bool:
    """Strategic decision with metacognition, capability check, and scoring"""
    pass

def claim_task(self, task_file: str) -> str:
    """Atomically claim a task using os.rename()"""
    pass

async def process_task(self, task_file: str):
    """Process a claimed task with error handling"""
    pass
```

#### Decision Making Methods

```python
async def can_handle(self, task) -> bool:
    """Binary capability check"""
    pass

async def calculate_fitness_score(self, task) -> int:
    """Calculate fitness score 1-10"""
    pass

async def metacognitive_check(self, task) -> Dict:
    """Internal reflection on whether to take this task"""
    pass
```

#### Task Management Methods

```python
def complete_task(self, task_file: str, result):
    """Move task to completed with results"""
    pass

def fail_task(self, task_file: str, error_message: str):
    """Move task to failed with error details"""
    pass

def dependencies_satisfied(self, task) -> bool:
    """Check if all task dependencies are completed"""
    pass
```

### Task Format Reference

#### Required Fields

```json
{
  "id": "string",           // Unique task identifier
  "description": "string",   // Human-readable task description
  "type": "string",         // Task type (complex_goal, file_operations, etc.)
  "created_at": "string"    // ISO 8601 timestamp
}
```

#### Optional Fields

```json
{
  "requirements": ["string"],     // Required agent capabilities
  "priority": "string",           // high, medium, low
  "context": {},                  // Additional context information
  "dependencies": ["string"],     // Task IDs this depends on
  "max_retries": 3,              // Maximum retry attempts
  "retry_count": 0               // Current retry count
}
```

### Environment Variables

#### Required

```bash
GOOGLE_API_KEY=your_api_key_here
# OR
GOOGLE_GENAI_USE_VERTEXAI=true
```

#### Optional

```bash
WORKSPACE_PATH=./workspace          # Workspace directory path
MAX_CONCURRENT_TASKS=3             # Max tasks per agent
POLLING_INTERVAL=2                 # Polling interval in seconds
LOG_LEVEL=INFO                     # Logging level
AGENT_DEBUG=false                  # Enable debug mode
```

---

## Contributing

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-agent`
3. **Follow the coding standards**:
   - Use the BaseAgent pattern for new agents
   - Implement three-LLM architecture
   - Include proper error handling
   - Add comprehensive documentation

### Adding New Agents

1. **Create agent directory**:
   ```bash
   mkdir new-agent-type
   cd new-agent-type
   mkdir agent_type_agent
   ```

2. **Implement agent class**:
   ```python
   from base_agent import BaseAgent
   
   class NewAgentType(BaseAgent):
       def __init__(self):
           super().__init__("NewAgentType", ["capability1", "capability2"])
       
       def get_threshold(self) -> int:
           return 6
       
       def get_executor_instruction(self) -> str:
           return "Specialized instructions for this agent type"
       
       def get_evaluator_instruction(self) -> str:
           return "Evaluation instructions"
       
       def get_metacognition_instruction(self) -> str:
           return "Metacognitive reflection instructions"
   ```

3. **Create run script**:
   ```python
   # run_autonomous.py
   import asyncio
   from agent_type_agent.agent import new_agent_type_agent
   
   async def main():
       await new_agent_type_agent.monitor_workspace()
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

4. **Add test tasks**:
   ```python
   # create_test_task.py
   import json
   import uuid
   from datetime import datetime
   
   def create_test_task():
       task = {
           "id": str(uuid.uuid4()),
           "description": "Test task for NewAgentType",
           "type": "new_agent_operations",
           "requirements": ["capability1"],
           "created_at": datetime.utcnow().isoformat()
       }
       
       with open("workspace/tasks/pending/test_task.json", "w") as f:
           json.dump(task, f, indent=2)
   
   if __name__ == "__main__":
       create_test_task()
   ```

### Testing Guidelines

1. **Unit Tests**: Test individual agent methods
2. **Integration Tests**: Test agent interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Test under load

### Documentation Standards

1. **Agent Documentation**: Document capabilities and use cases
2. **API Documentation**: Document all public methods
3. **Example Workflows**: Provide practical usage examples
4. **Troubleshooting**: Document common issues and solutions

### Code Review Process

1. **Submit pull request** with detailed description
2. **Include tests** for new functionality
3. **Update documentation** for any changes
4. **Follow style guidelines** and best practices

---

## License

[Add your license information here]

---

**Built with Google's Agent Development Kit (ADK)**  
*Autonomous. Intelligent. Coordinated.* 