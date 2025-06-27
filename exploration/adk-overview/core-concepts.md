# Core Concepts of Agent Development Kit (ADK)

The Agent Development Kit (ADK) is built around several key primitives and concepts that make it powerful and flexible for building sophisticated AI agents.

## Fundamental Primitives

### Agent
The fundamental worker unit designed for specific tasks. Agents can use language models (LlmAgent) for complex reasoning, or act as deterministic controllers of execution flow (workflow agents).

**Types of Agents:**
- **LlmAgent**: Powered by Large Language Models for reasoning and natural language tasks
- **SequentialAgent**: Executes sub-agents in a specific order
- **ParallelAgent**: Enables concurrent execution of multiple agents
- **LoopAgent**: Facilitates repeated execution with termination conditions
- **Custom Agents**: Built by extending BaseAgent for specialized logic

### Tool
Gives agents abilities beyond conversation, allowing them to interact with external APIs, search information, run code, or call other services.

**Tool Categories:**
- **FunctionTool**: Wraps Python functions for agent use
- **Built-in Tools**: Google Search, code execution, etc.
- **Google Cloud Tools**: Integration with Google Cloud services
- **MCP Tools**: Model Context Protocol compatible tools
- **OpenAPI Tools**: Generated from API specifications
- **AgentTool**: Allows one agent to use another as a tool

### Session Management
Handles the context of a single conversation, including its history (Events) and the agent's working memory (State).

**Components:**
- **Session**: Container for a conversation thread
- **State**: Temporary data storage for the current conversation
- **Events**: Communication units representing interactions
- **SessionService**: Manages session lifecycle and persistence

### Memory
Enables agents to recall information across multiple sessions, providing long-term context distinct from short-term session state.

**Implementation Options:**
- **InMemoryMemoryService**: For development and testing
- **Database-backed**: Persistent storage solutions
- **Vector databases**: For semantic search capabilities

## Architecture Components

### Event-Driven System
ADK operates on an event-driven architecture where Events are the fundamental units of communication.

**Event Types:**
- User messages
- Agent responses
- Tool calls and results
- State changes
- Control signals

### Runner
The execution engine that manages the agent lifecycle, orchestrates interactions, and coordinates with backend services.

**Responsibilities:**
- Managing execution flow
- Processing events
- Committing state changes
- Handling errors and exceptions
- Coordinating with services

### Callbacks
Custom code snippets that run at specific points in the agent's process, allowing for:
- Logging and monitoring
- Behavior modifications
- Custom validation
- Integration with external systems

## Multi-Agent Architecture

### Agent Hierarchy
ADK supports building applications with multiple specialized agents arranged hierarchically:

```
Coordinator Agent
├── Task Agent A
│   ├── Sub-agent A1
│   └── Sub-agent A2
└── Task Agent B
    ├── Sub-agent B1
    └── Sub-agent B2
```

### Communication Patterns

**Shared Session State**: Agents can share information through session state:
```python
# Agent A writes to state
context.state['data_key'] = processed_data

# Agent B reads from state
data = context.state.get('data_key')
```

**LLM-Driven Delegation**: Agents can transfer control dynamically:
```python
# Agent uses LLM to decide to transfer
transfer_to_agent(agent_name='specialist_agent')
```

**Explicit Invocation**: Agents can call other agents as tools:
```python
# Using AgentTool to invoke another agent
agent_tool = AgentTool(agent=target_agent)
```

## Orchestration Patterns

### Sequential Pipeline
```python
pipeline = SequentialAgent(
    name="DataPipeline",
    sub_agents=[validator, processor, reporter]
)
```

### Parallel Execution
```python
parallel_gather = ParallelAgent(
    name="ConcurrentFetch",
    sub_agents=[fetch_api1, fetch_api2]
)
```

### Iterative Processing
```python
refinement_loop = LoopAgent(
    name="IterativeRefiner",
    max_iterations=5,
    sub_agents=[processor, validator, decision_maker]
)
```

### Hierarchical Delegation
```python
coordinator = LlmAgent(
    name="TaskCoordinator",
    instruction="Delegate tasks to appropriate specialists",
    sub_agents=[specialist_a, specialist_b],
    tools=[agent_tool_c]
)
```

## Code Execution

ADK provides multiple code execution environments:

### Executor Types
- **ContainerCodeExecutor**: Isolated container execution for security
- **UnsafeLocalCodeExecutor**: Direct local execution (development only)
- **VertexAiCodeExecutor**: Managed execution via Google Cloud

### Security Considerations
- Container isolation for untrusted code
- Sandboxing capabilities
- Resource limitations
- Access controls

## State Management

### Session State
Temporary data for the current conversation:
- Key-value pairs (serializable)
- Session-scoped lifetime
- Shared among agents in the same session

### Persistent Memory
Long-term knowledge across sessions:
- Searchable information store
- Cross-session data retention
- Vector-based semantic search

### State Updates
```python
# Recommended methods for state updates
session_service.update_session_state(
    session_id=session.id,
    updates={"key": "value"}
)

# Within tool execution
def my_tool(session):
    session.state["key"] = "new_value"
    return "result"
```

## Integration Capabilities

### Model Support
- **Google Gemini**: Native optimization and integration
- **Anthropic Claude**: Direct API integration
- **OpenAI Models**: Via LiteLLM wrapper
- **Open Source Models**: Through various providers
- **Custom Models**: Extensible model interface

### External Services
- **Google Cloud**: Native integration with Vertex AI, etc.
- **REST APIs**: OpenAPI specification support
- **Databases**: Direct connection capabilities
- **Vector Stores**: Embedding and similarity search

### Framework Interoperability
- **LangChain Tools**: Compatibility wrapper
- **CrewAI Tools**: Integration support
- **MCP Protocol**: Standard tool communication
- **Custom Frameworks**: Extensible architecture

## Development Philosophy

### Code-First Approach
- Programmatic agent definition
- Version control friendly
- Reproducible configurations
- Clear separation of concerns

### Modularity
- Composable components
- Reusable agents and tools
- Clear interfaces
- Independent development

### Observability
- Built-in telemetry
- OpenTelemetry standard
- Tracing and monitoring
- Performance metrics

This architecture enables developers to build sophisticated AI applications that range from simple task automation to complex multi-agent collaborative systems. 