# Multi-Agent Systems in ADK

As agentic applications grow in complexity, structuring them as a single, monolithic agent can become challenging to develop, maintain, and reason about. The Agent Development Kit (ADK) supports building sophisticated applications by composing multiple, distinct agent instances into a **Multi-Agent System (MAS)**.

## Overview

In ADK, a multi-agent system is an application where different agents, often forming a hierarchy, collaborate or coordinate to achieve a larger goal. This architecture offers significant advantages:

- **Enhanced modularity**: Clear separation of concerns
- **Specialization**: Agents focused on specific domains
- **Reusability**: Agents can be shared across applications
- **Maintainability**: Easier to debug and update individual components
- **Structured control flows**: Dedicated workflow agents for orchestration

## Agent Composition Types

You can compose various types of agents derived from `BaseAgent`:

### LLM Agents
Agents powered by large language models for intelligent reasoning and language-based tasks.

### Workflow Agents
Specialized agents that manage execution flow of sub-agents:
- **SequentialAgent**: Executes sub-agents in order
- **ParallelAgent**: Executes sub-agents concurrently
- **LoopAgent**: Executes sub-agents in iterative loops

### Custom Agents
Agents with specialized, non-LLM logic for unique integrations.

## ADK Primitives for Agent Composition

### 1. Agent Hierarchy (Parent-Child Relationships)

The foundation is the parent-child relationship defined in `BaseAgent`.

**Key Characteristics:**
- Tree structure created by passing agent instances to `sub_agents`
- ADK automatically sets `parent_agent` attribute
- Single parent rule: agents can only have one parent
- Navigation using `agent.parent_agent` or `agent.find_agent(name)`

**Python Example:**
```python
from google.adk.agents import LlmAgent

# Define individual agents
greeter = LlmAgent(name="Greeter", model="gemini-2.0-flash")
task_doer = LlmAgent(name="TaskExecutor", model="gemini-2.0-flash")

# Create parent agent with sub-agents
coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    description="I coordinate greetings and tasks.",
    sub_agents=[greeter, task_doer]
)
```

**Java Example:**
```java
import com.google.adk.agents.LlmAgent;

LlmAgent greeter = LlmAgent.builder()
    .name("Greeter")
    .model("gemini-2.0-flash")
    .build();

LlmAgent coordinator = LlmAgent.builder()
    .name("Coordinator")
    .model("gemini-2.0-flash")
    .description("I coordinate greetings and tasks")
    .subAgents(greeter, taskDoer)
    .build();
```

### 2. Workflow Agents as Orchestrators

#### SequentialAgent
Executes sub-agents one after another in the specified order.

**Python Example:**
```python
from google.adk.agents import SequentialAgent, LlmAgent

step1 = LlmAgent(name="Step1_Fetch", output_key="data")
step2 = LlmAgent(name="Step2_Process", 
                instruction="Process data from state key 'data'.")

pipeline = SequentialAgent(name="MyPipeline", 
                          sub_agents=[step1, step2])
```

**Key Features:**
- Passes same InvocationContext sequentially
- Easy result passing via shared state
- Linear execution flow

#### ParallelAgent
Executes sub-agents concurrently with interleaved events.

**Python Example:**
```python
from google.adk.agents import ParallelAgent, LlmAgent

fetch_weather = LlmAgent(name="WeatherFetcher", output_key="weather")
fetch_news = LlmAgent(name="NewsFetcher", output_key="news")

gatherer = ParallelAgent(name="InfoGatherer", 
                        sub_agents=[fetch_weather, fetch_news])
```

**Key Features:**
- Modifies `InvocationContext.branch` for each child
- Shared `session.state` across all parallel children
- Use distinct keys to avoid race conditions

#### LoopAgent
Executes sub-agents sequentially in a loop with termination conditions.

**Python Example:**
```python
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from google.adk.events import Event, EventActions

class CheckCondition(BaseAgent):
    async def _run_async_impl(self, ctx):
        status = ctx.session.state.get("status", "pending")
        is_done = (status == "completed")
        yield Event(author=self.name, 
                   actions=EventActions(escalate=is_done))

process_step = LlmAgent(name="ProcessingStep")

poller = LoopAgent(
    name="StatusPoller",
    max_iterations=10,
    sub_agents=[process_step, CheckCondition(name="Checker")]
)
```

**Key Features:**
- Stops when `max_iterations` reached or agent escalates
- Same `InvocationContext` persists across iterations
- State changes persist between loops

### 3. Interaction & Communication Mechanisms

#### Shared Session State (`session.state`)
The primary way for agents to communicate passively within the same invocation.

**Python Example:**
```python
# Agent A writes to state
agent_A = LlmAgent(name="AgentA", 
                  instruction="Find the capital of France.", 
                  output_key="capital_city")

# Agent B reads from state
agent_B = LlmAgent(name="AgentB", 
                  instruction="Tell me about the city in 'capital_city'.")

pipeline = SequentialAgent(name="CityInfo", 
                          sub_agents=[agent_A, agent_B])
```

**Characteristics:**
- Asynchronous, passive communication
- Ideal for sequential pipelines
- Automatic via `output_key` property

#### LLM-Driven Delegation (Agent Transfer)
Dynamic routing based on LLM understanding.

**Setup Requirements:**
- Clear `instructions` on when to transfer
- Distinct `description`s for target agents
- Transfer scope configuration

**Python Example:**
```python
booking_agent = LlmAgent(name="Booker", 
                        description="Handles flight and hotel bookings.")
info_agent = LlmAgent(name="Info", 
                     description="Provides general information.")

coordinator = LlmAgent(
    name="Coordinator",
    instruction="Delegate booking tasks to Booker and info requests to Info.",
    sub_agents=[booking_agent, info_agent]
)
```

**Mechanism:**
- LLM generates `transfer_to_agent(agent_name='target')` call
- AutoFlow intercepts and routes execution
- Target found using `root_agent.find_agent()`

#### Explicit Invocation (`AgentTool`)
Treat another agent as a callable tool.

**Python Example:**
```python
from google.adk.tools import agent_tool

image_agent = ImageGeneratorAgent()
image_tool = agent_tool.AgentTool(agent=image_agent)

artist_agent = LlmAgent(
    name="Artist",
    instruction="Create prompts and use ImageGen tool to generate images.",
    tools=[image_tool]
)
```

**Characteristics:**
- Synchronous execution within parent's flow
- Explicit, controlled invocation
- Tool results returned to parent agent

## Common Multi-Agent Patterns

### 1. Coordinator/Dispatcher Pattern
Central coordinator routes requests to specialized agents.

**Structure:**
```python
billing_agent = LlmAgent(name="Billing", 
                        description="Handles billing inquiries.")
support_agent = LlmAgent(name="Support", 
                        description="Handles technical support.")

coordinator = LlmAgent(
    name="HelpDeskCoordinator",
    instruction="Route requests: Billing for payments, Support for technical.",
    sub_agents=[billing_agent, support_agent]
)
```

### 2. Sequential Pipeline Pattern
Multi-step process where output feeds into next step.

**Structure:**
```python
validator = LlmAgent(name="ValidateInput", 
                    instruction="Validate the input.", 
                    output_key="validation_status")
processor = LlmAgent(name="ProcessData", 
                    instruction="Process if validation_status is 'valid'.", 
                    output_key="result")
reporter = LlmAgent(name="ReportResult", 
                   instruction="Report result.")

data_pipeline = SequentialAgent(name="DataPipeline",
                               sub_agents=[validator, processor, reporter])
```

### 3. Parallel Fan-Out/Gather Pattern
Concurrent execution followed by result aggregation.

**Structure:**
```python
fetch_api1 = LlmAgent(name="API1Fetcher", output_key="api1_data")
fetch_api2 = LlmAgent(name="API2Fetcher", output_key="api2_data")

gather_concurrently = ParallelAgent(name="ConcurrentFetch",
                                   sub_agents=[fetch_api1, fetch_api2])

synthesizer = LlmAgent(name="Synthesizer",
                      instruction="Combine results from api1_data and api2_data.")

overall_workflow = SequentialAgent(name="FetchAndSynthesize",
                                  sub_agents=[gather_concurrently, synthesizer])
```

### 4. Hierarchical Task Decomposition
Multi-level tree breaking complex goals into simpler steps.

**Structure:**
```python
# Low-level agents
web_searcher = LlmAgent(name="WebSearch", 
                       description="Performs web searches.")
summarizer = LlmAgent(name="Summarizer", 
                     description="Summarizes text.")

# Mid-level agent
research_assistant = LlmAgent(
    name="ResearchAssistant",
    description="Finds and summarizes information.",
    tools=[AgentTool(agent=web_searcher), AgentTool(agent=summarizer)]
)

# High-level agent
report_writer = LlmAgent(
    name="ReportWriter",
    instruction="Write reports using ResearchAssistant.",
    tools=[AgentTool(agent=research_assistant)]
)
```

### 5. Review/Critique Pattern (Generator-Critic)
Generation followed by quality review.

**Structure:**
```python
generator = LlmAgent(name="DraftWriter",
                    instruction="Write a paragraph about subject X.",
                    output_key="draft_text")

reviewer = LlmAgent(name="FactChecker",
                   instruction="Review draft_text for accuracy. Output valid/invalid.",
                   output_key="review_status")

review_pipeline = SequentialAgent(name="WriteAndReview",
                                 sub_agents=[generator, reviewer])
```

### 6. Iterative Refinement Pattern
Progressive improvement until quality threshold met.

**Structure:**
```python
code_refiner = LlmAgent(name="CodeRefiner",
                       instruction="Generate/refine code based on requirements.",
                       output_key="current_code")

quality_checker = LlmAgent(name="QualityChecker",
                          instruction="Evaluate code quality. Output pass/fail.",
                          output_key="quality_status")

class CheckStatusAndEscalate(BaseAgent):
    async def _run_async_impl(self, ctx):
        status = ctx.session.state.get("quality_status", "fail")
        should_stop = (status == "pass")
        yield Event(author=self.name, 
                   actions=EventActions(escalate=should_stop))

refinement_loop = LoopAgent(
    name="CodeRefinementLoop",
    max_iterations=5,
    sub_agents=[code_refiner, quality_checker, 
               CheckStatusAndEscalate(name="StopChecker")]
)
```

### 7. Human-in-the-Loop Pattern
Integration of human intervention points.

**Conceptual Structure:**
```python
# Custom tool for human approval
approval_tool = FunctionTool(func=external_approval_tool)

prepare_request = LlmAgent(name="PrepareApproval",
                          instruction="Prepare approval request details.")

request_approval = LlmAgent(name="RequestHumanApproval",
                           instruction="Use approval tool with prepared details.",
                           tools=[approval_tool],
                           output_key="human_decision")

process_decision = LlmAgent(name="ProcessDecision",
                           instruction="Proceed based on human_decision.")

approval_workflow = SequentialAgent(name="HumanApprovalWorkflow",
                                   sub_agents=[prepare_request, 
                                             request_approval, 
                                             process_decision])
```

## Best Practices

### Design Principles
1. **Clear Responsibilities**: Each agent should have a focused, well-defined role
2. **Loose Coupling**: Minimize dependencies between agents
3. **State Management**: Use consistent state key naming conventions
4. **Error Handling**: Plan for failure scenarios and recovery
5. **Testing**: Test individual agents and complete workflows

### Naming Conventions
```python
# Use prefixes for state organization
"tool_name.key"     # Tool-specific data
"agent.key"         # Agent-specific data  
"user.key"          # User-specific data
```

### Communication Guidelines
- Use `output_key` for sequential data passing
- Implement clear transfer conditions for LLM delegation
- Design AgentTool interfaces for explicit invocation
- Handle race conditions in parallel execution

### Performance Considerations
- Monitor token usage in complex hierarchies
- Use workflow agents for deterministic flows
- Consider memory limitations with deep hierarchies
- Profile execution times for optimization

## Advanced Topics

### Dynamic Agent Creation
Agents can be created and composed at runtime based on requirements.

### Cross-Agent Tool Sharing
Tools can be shared across multiple agents in the hierarchy.

### Custom Communication Protocols
Implement specialized communication patterns beyond the built-in mechanisms.

### Agent Discovery and Registry
Build systems for automatic agent discovery and composition.

## Debugging Multi-Agent Systems

### Tracing Execution
- Use ADK's built-in tracing capabilities
- Monitor event flows between agents
- Track state changes across the hierarchy

### Common Issues
- State key conflicts between agents
- Infinite loops in agent delegation
- Resource contention in parallel execution
- Memory leaks in long-running systems

Multi-agent systems in ADK provide powerful capabilities for building sophisticated, modular, and maintainable AI applications. By understanding these patterns and primitives, you can design systems that scale from simple task automation to complex collaborative workflows. 