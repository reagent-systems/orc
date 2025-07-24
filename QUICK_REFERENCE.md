# ORC Multi-Agent System - Quick Reference

## 🚀 Quick Start

### 1. Setup
```bash
# Clone and setup
git clone <repository>
cd orc
python3 setup_multi_agent.py

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start Agents
```bash
# Terminal 1 - Task Breakdown
cd task-breakdown-agent && python3 run_autonomous.py

# Terminal 2 - Search Operations  
cd google-search-agent && python3 run_autonomous.py

# Terminal 3 - File Operations
cd file-agent && python3 run_autonomous.py

# Terminal 4 - Terminal Operations
cd terminal-agent && python3 run_autonomous.py
```

### 3. Create Test Tasks
```bash
# Create complex tasks for breakdown
cd task-breakdown-agent && python3 create_test_task.py

# Create file operation tasks
cd file-agent && python3 create_test_task.py

# Create search tasks
cd google-search-agent && python3 create_test_task.py

# Create terminal tasks
cd terminal-agent && python3 create_test_task.py
```

## 📋 Task Creation

### Basic Task Format
```json
{
  "id": "unique-uuid",
  "description": "Your task description",
  "type": "complex_goal",
  "requirements": ["task_decomposition", "orchestration"],
  "priority": "high",
  "context": {
    "original_goal": "Your main objective"
  },
  "created_at": "2024-01-01T10:00:00Z"
}
```

### Quick Task Creation
```bash
# Create a task file
echo '{
  "id": "test_task",
  "description": "Research Python web frameworks",
  "type": "complex_goal",
  "requirements": ["task_decomposition"],
  "priority": "high"
}' > workspace/tasks/pending/test_task.json
```

## 🔍 Monitoring Commands

### Check System Status
```bash
# Agent heartbeats
ls -la workspace/agents/

# Task status
ls -la workspace/tasks/pending/
ls -la workspace/tasks/active/
ls -la workspace/tasks/completed/
ls -la workspace/tasks/failed/

# Real-time monitoring
watch -n 1 'ls -la workspace/tasks/*/'
```

### Debug Commands
```bash
# Check agent heartbeats
find workspace/agents/ -name "*.json" -exec cat {} \;

# Check for stuck tasks
find workspace/tasks/active/ -mmin +30 -name "*.json"

# Validate JSON
python3 -m json.tool workspace/tasks/pending/task.json
```

## 🤖 Agent Types & Capabilities

### Priority 1 Agents (Core)
| Agent | Capabilities | Threshold | Purpose |
|-------|-------------|-----------|---------|
| **TaskBreakdownAgent** | `task_decomposition`, `orchestration`, `planning` | 6 | Breaks down complex tasks |
| **SearchAgent** | `web_search`, `google_search`, `research` | 6 | Web research and search |
| **FileAgent** | `file_operations`, `code_analysis`, `text_processing` | 6 | File and code operations |
| **TerminalAgent** | `command_execution`, `system_operations` | 6 | System commands |

### Priority 2 Agents (Ready)
| Agent | Capabilities | Purpose |
|-------|-------------|---------|
| **GitAgent** | `version_control`, `code_review` | Git operations |
| **TestAgent** | `testing`, `validation` | Automated testing |
| **DatabaseAgent** | `database_operations` | Database management |
| **APIAgent** | `api_integration` | API interactions |

## ⚙️ Configuration

### Environment Variables
```bash
# Required
GOOGLE_API_KEY=your_api_key_here
# OR
GOOGLE_GENAI_USE_VERTEXAI=true

# Optional
WORKSPACE_PATH=./workspace
MAX_CONCURRENT_TASKS=3
POLLING_INTERVAL=2
LOG_LEVEL=INFO
AGENT_DEBUG=false
```

### Workspace Structure
```
workspace/
├── tasks/
│   ├── pending/     # New tasks
│   ├── active/      # Being processed
│   ├── completed/   # Finished tasks
│   └── failed/      # Failed tasks
├── agents/          # Heartbeat files
├── context/         # Task results
└── results/         # Final outputs
```

## 🔧 Common Tasks

### Research Project
```json
{
  "id": "research_project",
  "description": "Research modern Python web frameworks, compare performance, create guide",
  "type": "complex_goal",
  "requirements": ["task_decomposition", "orchestration"],
  "priority": "high",
  "context": {
    "original_goal": "Create web framework comparison guide"
  }
}
```

### Code Generation
```json
{
  "id": "code_generation",
  "description": "Create Python API client for GitHub REST API",
  "type": "file_operations",
  "requirements": ["file_operations", "code_analysis"],
  "priority": "medium",
  "context": {
    "original_goal": "Build GitHub API integration"
  }
}
```

### System Setup
```json
{
  "id": "system_setup",
  "description": "Set up Python development environment with virtual env and dependencies",
  "type": "terminal_operations",
  "requirements": ["command_execution", "system_operations"],
  "priority": "high",
  "context": {
    "original_goal": "Prepare development environment"
  }
}
```

## 🚨 Troubleshooting

### Agents Not Starting
```bash
# Check API key
cat .env | grep GOOGLE_API_KEY

# Check ADK installation
pip list | grep google-adk

# Check workspace permissions
ls -la workspace/
```

### Tasks Not Being Claimed
```bash
# Check agent capabilities
find workspace/agents/ -name "*.json" -exec cat {} \;

# Check task requirements
python3 -m json.tool workspace/tasks/pending/task.json

# Check dependencies
ls -la workspace/tasks/completed/
```

### Performance Issues
```bash
# Reduce polling frequency
export POLLING_INTERVAL=5

# Limit concurrent tasks
export MAX_CONCURRENT_TASKS=2

# Enable debug mode
export AGENT_DEBUG=true
```

## 📊 Task Lifecycle

1. **Pending** → Task waiting to be claimed
2. **Active** → Task being processed (agent_id prefix)
3. **Completed** → Task finished with results
4. **Failed** → Task failed with retry logic

### Task States
```bash
# Check task status
find workspace/tasks/ -name "*.json" -exec grep -l "status" {} \;

# View completed results
ls -la workspace/tasks/completed/

# Check failed tasks
ls -la workspace/tasks/failed/
```

## 🎯 Decision Making Process

Each agent uses a three-step decision process:

1. **Metacognitive Reflection** - Internal reflection on task suitability
2. **Capability Check** - Binary assessment of technical ability  
3. **Fitness Scoring** - Numerical rating (1-10) of task suitability

### Thresholds
- **TaskBreakdownAgent**: 6 (moderately eager)
- **SearchAgent**: 6
- **FileAgent**: 6  
- **TerminalAgent**: 6

## 🔄 Advanced Features

### Self-Extension
System can create new agents when missing capabilities:
1. **Detection** - TaskBreakdownAgent identifies missing capabilities
2. **Research** - SearchAgent researches implementation patterns
3. **Generation** - FileAgent creates new agent code
4. **Deployment** - TerminalAgent deploys and registers new agent

### Goal Validation
Results are validated against original goals using metacognitive LLM.

### Atomic Coordination
Race-condition-free task claiming using `os.rename()`.

## 📚 Documentation

- **[Complete Documentation](DOCUMENTATION.md)** - Full system documentation
- **[README](README.md)** - System overview and quick start
- **[Architecture Design](outline/multi-agent-orchestration-design.md)** - Detailed architecture

## 🆘 Getting Help

### Common Issues
1. **API Key Issues** - Check `.env` configuration
2. **ADK Installation** - Run `pip install google-adk`
3. **Workspace Permissions** - Check directory permissions
4. **Task Dependencies** - Verify completed dependencies

### Debug Mode
```bash
export AGENT_DEBUG=true
export LOG_LEVEL=DEBUG
```

### Performance Monitoring
```bash
# Monitor task completion rate
watch -n 5 'echo "Pending: $(ls workspace/tasks/pending/ | wc -l)"; echo "Active: $(ls workspace/tasks/active/ | wc -l)"; echo "Completed: $(ls workspace/tasks/completed/ | wc -l)"; echo "Failed: $(ls workspace/tasks/failed/ | wc -l)"'
```

---

**Quick Reference for ORC Multi-Agent Orchestration System**  
*For complete documentation, see [DOCUMENTATION.md](DOCUMENTATION.md)* 