# Multi-Agent Orchestration System Design

## Core Architecture

### Workspace Structure
```
workspace/
├── tasks/
│   ├── pending/         # New tasks awaiting pickup
│   ├── active/          # Tasks being worked on (agent_id in filename)
│   ├── completed/       # Finished tasks with results
│   └── failed/          # Tasks that couldn't complete
├── agents/
│   └── registry.json    # Active agent registry
├── context/             # Shared context and state
└── results/             # Final deliverables
```

### Task Format
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
    "created_by": "TaskBreakdownAgent_12ab34cd",
    "created_at": "2025-01-15T10:00:00Z",
    "claimed_by": null,
    "claimed_at": null
}
```

## Base Agent Architecture

```python
class BaseAgent:
    def __init__(self, agent_type: str, capabilities: List[str]):
        self.agent_id = f"{agent_type}_{uuid4().hex[:8]}"
        self.agent_type = agent_type
        self.capabilities = capabilities
        
        # Three-LLM architecture
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
        self.workspace_path = "workspace"
    
    # Main agent loop
    async def monitor_workspace(self):
        while True:
            pending_tasks = self.scan_pending_tasks()
            
            for task_file in pending_tasks:
                task = self.load_task(task_file)
                
                if await self.should_handle(task):
                    if self.claim_task(task_file):
                        await self.process_task(task)
                        break
            
            await asyncio.sleep(1)
    
    # LLM-based decision making
    async def should_handle(self, task) -> bool:
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
    
    async def can_handle(self, task) -> bool:
        prompt = f"""
        Task: {task['description']}
        Type: {task.get('type', 'unknown')}
        Requirements: {task.get('requirements', [])}
        My capabilities: {self.capabilities}
        
        Can I technically execute this task? Answer YES or NO only.
        """
        response = await self.evaluator.process(prompt)
        return "YES" in response.upper()
    
    async def calculate_fitness_score(self, task) -> int:
        prompt = f"""
        Task: {task['description']}
        Current workload: {len(self.active_tasks)} tasks
        My specialization: {self.agent_type}
        
        Rate my fitness for this task (1-10). Return only the number.
        """
        response = await self.evaluator.process(prompt)
        return int(re.search(r'\d+', response).group())
    
    async def metacognitive_check(self, task) -> Dict:
        recent_actions = self.get_recent_actions()
        workspace_state = self.get_workspace_summary()
        
        prompt = f"""
        I'm considering taking this task: {task['description']}
        
        My recent actions: {recent_actions}
        Current workspace: {workspace_state}
        Original goal: {task.get('context', {}).get('original_goal')}
        
        Internal reflection:
        1. Have I done something similar recently?
        2. Will this actually progress the goal?
        3. Am I creating redundant work?
        4. Should I step back and let others handle this?
        
        Decision: PROCEED or STEP_BACK
        """
        
        response = await self.metacognition.process(prompt)
        return {'proceed': "PROCEED" in response.upper(), 'reasoning': response}
    
    # Atomic task claiming
    def claim_task(self, task_file: str) -> bool:
        claimed_file = task_file.replace('pending', 'active').replace('.json', f'_{self.agent_id}.json')
        
        try:
            os.rename(task_file, claimed_file)
            return True
        except FileNotFoundError:
            return False
    
    # Task processing with goal validation
    async def process_task(self, task):
        try:
            result = await self.executor.process(task)
            
            if await self.validates_goal_progress(task, result):
                self.complete_task(task, result)
            else:
                self.fail_task(task, "Result doesn't advance original goal")
        except Exception as e:
            self.fail_task(task, str(e))
    
    async def validates_goal_progress(self, task, result) -> bool:
        original_goal = task.get('context', {}).get('original_goal')
        if not original_goal:
            return True
        
        prompt = f"""
        Original goal: {original_goal}
        Task completed: {task['description']}
        Task result: {result}
        
        Does this result meaningfully advance the original goal? YES or NO.
        """
        
        response = await self.metacognition.process(prompt)
        return "YES" in response.upper()
```

## Specialized Agent Types

### TaskBreakdownAgent
```python
class TaskBreakdownAgent(BaseAgent):
    def __init__(self):
        super().__init__("TaskBreakdownAgent", ["task_decomposition", "planning"])
        
        self.deduplicator = LlmAgent(
            instruction="Compare tasks for semantic similarity. Answer YES if duplicate."
        )
    
    def get_threshold(self) -> int:
        return 8  # High threshold - only genuinely complex tasks
    
    async def should_handle(self, task):
        # Check if we need to create a new agent type first
        if await self.requires_missing_agent(task):
            await self.create_agent_creation_workflow(task)
            return False
        
        return await super().should_handle(task)
    
    async def requires_missing_agent(self, task) -> bool:
        prompt = f"""
        Task: {task['description']}
        Current agents: SearchAgent, FileAgent, TerminalAgent, TaskBreakdownAgent
        
        Does this require capabilities none of our agents have?
        Answer YES if we need a new agent type.
        """
        response = await self.evaluator.process(prompt)
        return "YES" in response.upper()
    
    async def create_agent_creation_workflow(self, original_task):
        agent_type = await self.identify_needed_agent_type(original_task)
        
        workflow_tasks = [
            {
                "description": f"Research {agent_type} implementation patterns",
                "type": "research",
                "requirements": ["web_search"],
                "context": {"original_goal": original_task['description'], "agent_type": agent_type}
            },
            {
                "description": f"Write {agent_type} code with ADK integration",
                "type": "code_generation",
                "requirements": ["file_operations"],
                "context": {"original_goal": original_task['description'], "agent_type": agent_type}
            },
            {
                "description": f"Test and deploy {agent_type}",
                "type": "deployment",
                "requirements": ["command_execution"],
                "context": {"original_goal": original_task['description'], "agent_type": agent_type}
            },
            {
                "description": original_task['description'],
                "type": original_task['type'],
                "context": original_task['context']
            }
        ]
        
        for task in workflow_tasks:
            self.save_task_to_pending(task)
    
    async def create_subtasks(self, parent_task):
        subtasks = await self.executor.breakdown(parent_task)
        recent_tasks = self.get_recent_workspace_tasks()
        
        unique_subtasks = []
        for subtask in subtasks:
            if not await self.is_semantic_duplicate(subtask, recent_tasks):
                unique_subtasks.append(subtask)
                self.save_task_to_pending(subtask)
        
        return unique_subtasks
    
    async def is_semantic_duplicate(self, new_task, existing_tasks) -> bool:
        prompt = f"""
        New task: {new_task['description']}
        Recent tasks: {[t['description'] for t in existing_tasks[-20:]]}
        
        Is the new task essentially the same work? YES or NO.
        """
        response = await self.deduplicator.process(prompt)
        return "YES" in response.upper()
```

### SearchAgent
```python
class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("SearchAgent", ["web_search", "research"])
        self.search_tool = GoogleSearchTool()
    
    def get_threshold(self) -> int:
        return 6
    
    def get_executor_instruction(self) -> str:
        return """Perform web searches with focus on:
        
        For agent creation tasks:
        - Find ADK documentation and examples
        - Search for implementation patterns  
        - Look up best practices for the required capabilities
        - Find relevant tools and libraries
        
        Provide comprehensive research for building new agents."""
```

### FileAgent
```python
class FileAgent(BaseAgent):
    def __init__(self):
        super().__init__("FileAgent", ["file_operations", "code_editing"])
    
    def get_threshold(self) -> int:
        return 6
    
    def get_executor_instruction(self) -> str:
        return """Handle file operations including creating new ADK agents.
        
        When creating agents:
        1. Use BaseAgent template from the system
        2. Implement required capabilities based on task context
        3. Follow ADK patterns for LLM integration
        4. Include proper error handling and logging
        5. Create appropriate directory structure
        
        For agent creation tasks, generate complete, functional agent code."""
    
    async def create_new_agent(self, agent_spec):
        """Generate new agent based on specifications"""
        template = self.load_base_agent_template()
        
        agent_code = await self.executor.process(f"""
        Create ADK agent:
        Type: {agent_spec['type']}
        Capabilities: {agent_spec['capabilities']}
        Tools: {agent_spec['tools']}
        
        Base template: {template}
        
        Generate complete agent.py with proper ADK integration.
        """)
        
        agent_dir = f"{agent_spec['type'].lower()}-agent"
        os.makedirs(agent_dir, exist_ok=True)
        
        with open(f"{agent_dir}/agent.py", 'w') as f:
            f.write(agent_code)
        
        with open(f"{agent_dir}/__init__.py", 'w') as f:
            f.write("from . import agent")
        
        AgentRegistry.register_new_agent(agent_spec['type'], agent_dir, agent_spec['capabilities'])
```

### TerminalAgent
```python
class TerminalAgent(BaseAgent):
    def __init__(self):
        super().__init__("TerminalAgent", ["command_execution", "system_operations"])
    
    def get_threshold(self) -> int:
        return 6
    
    def get_executor_instruction(self) -> str:
        return """Execute system commands and operations including:
        
        For agent deployment:
        - Start new agent processes
        - Install dependencies
        - Run tests and validation
        - Configure environment
        
        Always ensure safe command execution and proper error handling."""
```

## Agent Registry System

```python
class AgentRegistry:
    @staticmethod
    def register_new_agent(agent_type: str, directory: str, capabilities: List[str]):
        registry_path = "workspace/agents/registry.json"
        registry = AgentRegistry.load_registry()
        
        registry['active_agents'].append({
            "type": agent_type,
            "capabilities": capabilities,
            "directory": directory,
            "status": "active"
        })
        
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
    
    @staticmethod
    def get_available_capabilities() -> List[str]:
        registry = AgentRegistry.load_registry()
        capabilities = []
        for agent in registry['active_agents']:
            capabilities.extend(agent['capabilities'])
        return list(set(capabilities))
    
    @staticmethod
    def load_registry():
        registry_path = "workspace/agents/registry.json"
        if os.path.exists(registry_path):
            with open(registry_path, 'r') as f:
                return json.load(f)
        return {"active_agents": []}
```

## System Coordination

### Loop Prevention Strategy
1. **Natural equilibrium**: Specialists claim appropriately-sized tasks, preventing breakdown agents from over-decomposing
2. **Metacognitive awareness**: Agents reflect on their actions and question redundant work
3. **LLM semantic deduplication**: Prevents creation of duplicate tasks
4. **Emergency depth limit**: Hard stop at task depth 5

### Task Flow Process
1. User drops JSON task in `workspace/tasks/pending/`
2. All agents evaluate task fitness via LLM
3. Best-fit agent claims task atomically via `os.rename()`
4. Agent processes task, validates result advances original goal
5. Results saved to `completed/` or new subtasks created in `pending/`

### Self-Extension Capability
1. TaskBreakdownAgent detects missing capabilities
2. Creates workflow: research → code generation → testing → deployment
3. FileAgent generates new agent code using BaseAgent template
4. TerminalAgent deploys and registers new agent
5. Original task retried with new agent capabilities

### Manual Startup Process
```bash
# Start agents in separate terminals
cd google-search-agent && adk web
cd task-breakdown-agent && adk web  
cd file-agent && adk web
cd terminal-agent && adk web
```

## User Interaction

### Task Initiation
```bash
# User drops task file into workspace
echo '{
  "description": "Build a REST API for user management",
  "type": "software_development",
  "context": {
    "requirements": ["CRUD operations", "authentication", "validation"],
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
  }
}' > workspace/tasks/pending/build_user_api.json
```

### Goal Achievement Tracking
Each task result is validated against the original goal using LLM metacognition to ensure meaningful progress.

## Key Principles

1. **No central orchestrator**: Pure peer-to-peer coordination
2. **Manual agent startup**: You control which agents run
3. **Shared workspace**: Single folder all agents monitor
4. **File-based communication**: Tasks and results via JSON files
5. **Autonomous task selection**: Agents pick work they can handle
6. **Emergent workflows**: Complex tasks arise from simple agent interactions
7. **LLM-based decision making**: Embedded evaluator agents for smart choices
8. **Atomic file operations**: Race-condition-free task claiming
9. **Self-extending system**: Creates new agents when needed
10. **Goal validation**: Results must advance original objectives

All agents monitor the same workspace directory. System extends itself by creating new agents when encountering tasks requiring capabilities it lacks. Pure LLM-based decision making throughout with file-based atomic coordination. 