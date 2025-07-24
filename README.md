# Multi-Agent Orchestration System (ORC)

A sophisticated autonomous multi-agent system built with Google's Agent Development Kit (ADK). This system enables multiple AI agents to work together autonomously to accomplish complex tasks through intelligent task decomposition and coordination.

## 🎯 **System Overview**

The ORC (Orchestration) system is a **peer-to-peer multi-agent architecture** where agents autonomously monitor a shared workspace, claim tasks they're equipped to handle, and coordinate through file-based communication. No central orchestrator is needed - agents self-organize through intelligent decision making.

### **Core Philosophy**
- **Autonomous Operation**: Agents decide independently what tasks to take
- **Natural Equilibrium**: Specialist agents prevent infinite task breakdown loops
- **LLM-Based Intelligence**: Each agent uses three LLMs for execution, evaluation, and metacognition
- **Atomic Coordination**: Race-condition-free task claiming using `os.rename()`
- **Goal Preservation**: Original objectives are maintained through task decomposition chains

## 🤖 **Priority 1 Base Agents**

### **TaskBreakdownAgent** 🧩
- **Purpose**: Decomposes complex tasks into actionable sequential steps
- **Capabilities**: `task_decomposition`, `orchestration`, `planning`
- **Key Features**:
  - Analyzes task complexity before breakdown
  - Creates subtasks with proper dependencies
  - Prevents infinite breakdown loops through intelligence
  - Preserves original goal context throughout decomposition

### **SearchAgent** 🔍
- **Purpose**: Handles all web search and research operations
- **Capabilities**: `web_search`, `google_search`, `research`
- **Key Features**:
  - Multiple search types (general, news, academic, tutorials, local)
  - Result analysis and summarization
  - Research task coordination

### **FileAgent** 📁
- **Purpose**: Manages all file operations and code generation
- **Capabilities**: `file_operations`, `code_analysis`, `text_processing`, `agent_generation`
- **Key Features**:
  - Complete file operations (read, write, create, delete, copy)
  - Code analysis and syntax checking
  - New agent code generation
  - Text processing and document creation

### **TerminalAgent** ⚡
- **Purpose**: Executes system commands and manages environments
- **Capabilities**: `command_execution`, `system_operations`, `cli_navigation`
- **Key Features**:
  - Safe command execution with built-in safety checks
  - System information gathering
  - Environment setup and package installation
  - Process management and monitoring

## 🏗️ **System Architecture**

### **Three-LLM Agent Architecture**
Each agent contains three specialized LLMs:

1. **Executor LLM**: Performs the actual task work
2. **Evaluator LLM**: Assesses task fitness and capability matching
3. **Metacognition LLM**: Provides self-reflection and prevents infinite loops

### **Workspace Structure**
```
workspace/
├── tasks/
│   ├── pending/     # New tasks waiting to be claimed
│   ├── active/      # Tasks currently being processed  
│   ├── completed/   # Successfully completed tasks
│   └── failed/      # Failed tasks (with retry logic)
├── agents/          # Agent heartbeat/status files
├── context/         # Task results for future reference
└── results/         # Final outputs and artifacts
```

### **Task Flow**
1. **Task Creation**: User drops JSON task files in `workspace/tasks/pending/`
2. **Agent Monitoring**: All agents continuously scan for new tasks
3. **Capability Evaluation**: Agents assess if they can handle each task
4. **Atomic Claiming**: First suitable agent atomically claims task via `os.rename()`
5. **Task Processing**: Agent processes task with metacognitive oversight
6. **Result Storage**: Completed tasks moved to appropriate folder with results
7. **Context Preservation**: Results saved for future task context

### **Task Decomposition Flow**
```
Complex Task → TaskBreakdownAgent → Subtasks → Specialist Agents → Results
```

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.8+
- Google API Key (Gemini) or Vertex AI access
- ADK installed (`pip install google-adk`)

### **Setup**
1. **Clone and Setup Environment**:
   ```bash
   git clone <repository>
   cd orc
   python3 setup_multi_agent.py
   ```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`
   - Add your Google API keys:
     ```
     GOOGLE_API_KEY=your_api_key_here
     # OR for Vertex AI:
     GOOGLE_GENAI_USE_VERTEXAI=true
     ```

3. **Start Agents** (each in separate terminal):
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

### **Test the System**
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

## 📝 **Creating Tasks**

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

### **Task Types**
- `complex_goal`: Multi-step tasks requiring breakdown
- `web_search`: Search and research tasks
- `file_operations`: File system and code tasks
- `terminal_operations`: Command execution tasks

## 🔧 **Configuration**

Environment variables (`.env`):
```bash
# Required: Google API access
GOOGLE_API_KEY=your_key_here
# OR
GOOGLE_GENAI_USE_VERTEXAI=true

# Optional: System tuning
WORKSPACE_PATH=./workspace
MAX_CONCURRENT_TASKS=3
POLLING_INTERVAL=2
```

## 📊 **Monitoring**

### **Agent Status**
Check `workspace/agents/` for agent heartbeat files showing:
- Agent status and capabilities
- Active task count
- Last heartbeat timestamp

### **Task Progress**
Monitor task folders:
- `pending/`: Tasks waiting to be claimed
- `active/`: Tasks being processed (prefixed with agent ID)
- `completed/`: Finished tasks with results
- `failed/`: Failed tasks with error details

### **Task Context**
Check `workspace/context/` for task results and context information that agents use for future tasks.

## 🛡️ **Safety Features**

- **Command Safety**: TerminalAgent blocks dangerous commands
- **Timeout Protection**: All operations have timeout limits
- **Retry Logic**: Failed tasks automatically retry with backoff
- **Metacognitive Oversight**: Agents self-reflect before taking actions
- **Loop Prevention**: Natural equilibrium prevents infinite task breakdown

## 🧩 **Extension Points**

The system is designed for easy extension:

1. **New Agent Types**: Follow the BaseAgent pattern
2. **Custom Tools**: Extend ADK BaseTool for agent capabilities  
3. **Task Types**: Add new task schemas and processing logic
4. **Coordination Patterns**: Implement new agent interaction patterns

## 📚 **Documentation**

- **[Complete Documentation](DOCUMENTATION.md)** - Comprehensive system documentation
- **[Quick Reference](QUICK_REFERENCE.md)** - Essential commands and troubleshooting
- **[Architecture Design](outline/multi-agent-orchestration-design.md)** - Detailed system architecture
- **[Agent Types](outline/agent-types-needed.md)** - Full agent capability matrix
- **[Final Architecture](outline/final-architecture.md)** - Implementation architecture
- **[ADK Exploration](exploration/)** - ADK research and documentation

## 🔮 **Next Steps**

**Priority 2 Agents** (ready for implementation):
- GitAgent, TestAgent, DatabaseAgent, APIAgent

**Priority 3 Agents**:
- EmailAgent, SlackAgent, DataAnalysisAgent, DocumentAgent

**Advanced Features**:
- Web UI for monitoring and control
- Agent performance analytics
- Dynamic agent spawning
- Cross-agent memory sharing

## 📄 **License**

[Add your license here]

## 🤝 **Contributing**

[Add contribution guidelines here]

---

**Built with Google's Agent Development Kit (ADK)**  
*Autonomous. Intelligent. Coordinated.* 