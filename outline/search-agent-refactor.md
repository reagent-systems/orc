# Search Agent Refactor for Multi-Agent System

## Current Issues

The existing Google Search agent has fundamental incompatibilities with our multi-agent orchestration system:

1. **Wrong base class**: Uses `LlmAgent` instead of `BaseAgent`
2. **Missing architecture**: No three-LLM system (executor, evaluator, metacognition)
3. **No workspace integration**: Cannot monitor or claim tasks
4. **Broken helper functions**: Return metadata instead of performing searches
5. **No autonomous behavior**: Designed for direct user interaction only

## Required Refactor

### New Architecture
```python
class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("SearchAgent", ["web_search", "research", "information_retrieval"])
        
        # Google Search tool integration
        self.google_search_tool = GoogleSearchTool(
            name="google_search"
        )
        
        # Research capabilities for agent creation tasks
        self.research_capabilities = [
            "adk_documentation",
            "implementation_patterns", 
            "best_practices",
            "tool_libraries",
            "framework_examples"
        ]
    
    def get_threshold(self) -> int:
        return 6  # Eager to handle search tasks
    
    def get_executor_instruction(self) -> str:
        return """You are a web search specialist that provides comprehensive research capabilities.
        
        Core responsibilities:
        - Perform Google web searches using the google_search tool
        - Research current information, news, and technical documentation
        - Find tutorials, guides, and implementation examples
        - Search for academic papers and scholarly content
        - Locate local businesses and services when needed
        
        For multi-agent system tasks:
        - Research ADK documentation and examples for agent creation
        - Find implementation patterns for new agent types
        - Search for tool libraries and frameworks
        - Look up best practices and coding standards
        - Find relevant technical documentation
        
        Always provide:
        - Comprehensive search results with source links
        - Summary of key findings
        - Relevance assessment for the original goal
        - Suggestions for follow-up searches if needed
        
        Use the google_search tool for all web searches."""
    
    def get_evaluator_instruction(self) -> str:
        return """Evaluate search and research tasks for the SearchAgent.
        
        I can handle tasks requiring:
        - Web search and information retrieval
        - Research on technical topics
        - Finding documentation and examples
        - News and current events research
        - Academic paper searches
        - Local business searches
        
        Rate task fitness (1-10) based on:
        - How well it matches search/research needs
        - Complexity of information required
        - Current workload capacity
        
        Answer YES/NO for capability and provide fitness scores."""
    
    def get_metacognition_instruction(self) -> str:
        return """Provide self-reflection for SearchAgent decisions.
        
        Before taking search tasks, consider:
        - Have I searched for similar information recently?
        - Will this search provide new value or duplicate existing work?
        - Is this search specific enough to be useful?
        - Does this advance the original goal?
        
        Prevent redundant searches and ensure meaningful contribution to multi-agent workflows."""
```

### Enhanced Search Methods
```python
async def perform_web_search(self, query: str, search_type: str = "general") -> Dict:
    """Actually perform web search using Google Search tool"""
    
    # Enhance query based on search type
    enhanced_query = await self.enhance_search_query(query, search_type)
    
    # Perform actual search
    search_results = await self.google_search_tool.search(enhanced_query)
    
    # Process and summarize results
    summary = await self.executor.process(f"""
    Search query: {enhanced_query}
    Search results: {search_results}
    
    Provide a comprehensive summary including:
    1. Key findings from the search results
    2. Most relevant and credible sources
    3. Direct links to important resources
    4. Assessment of information quality and recency
    5. Suggestions for follow-up searches if needed
    
    Focus on actionable information that advances the original goal.
    """)
    
    return {
        "status": "success",
        "query": enhanced_query,
        "original_query": query,
        "search_type": search_type,
        "results": search_results,
        "summary": summary,
        "sources": self.extract_sources(search_results)
    }

async def enhance_search_query(self, query: str, search_type: str) -> str:
    """Use LLM to enhance search queries for better results"""
    
    enhancement_prompt = f"""
    Original search query: {query}
    Search type: {search_type}
    
    Enhance this query for better Google search results:
    
    For "agent_creation" type: Add terms like "ADK", "implementation", "example", "tutorial"
    For "news" type: Add "recent", "latest", current year
    For "academic" type: Add "research", "paper", "study", "journal"
    For "tutorial" type: Add "how to", "guide", "tutorial", "step by step"
    For "local" type: Add location context and "near me"
    
    Return the enhanced query only.
    """
    
    enhanced = await self.evaluator.process(enhancement_prompt)
    return enhanced.strip()

async def research_for_agent_creation(self, agent_type: str, capabilities: List[str]) -> Dict:
    """Specialized research for creating new agents"""
    
    research_queries = [
        f"ADK {agent_type} agent implementation example",
        f"Google Agent Development Kit {capabilities[0]} tutorial", 
        f"{agent_type} agent best practices ADK framework",
        f"Google ADK tools for {' '.join(capabilities)}"
    ]
    
    all_research = []
    for query in research_queries:
        result = await self.perform_web_search(query, "agent_creation")
        all_research.append(result)
    
    # Synthesize research findings
    synthesis = await self.executor.process(f"""
    Research goal: Create {agent_type} with capabilities {capabilities}
    
    Research results: {all_research}
    
    Synthesize findings into actionable guidance:
    1. Key implementation patterns found
    2. Required dependencies and tools
    3. Best practices and recommendations  
    4. Code examples and templates
    5. Common pitfalls to avoid
    
    Focus on practical information for building the agent.
    """)
    
    return {
        "agent_type": agent_type,
        "capabilities": capabilities,
        "research_results": all_research,
        "synthesis": synthesis,
        "implementation_guidance": synthesis
    }
```

### Task Processing Integration
```python
async def process_task(self, task):
    """Process search tasks within multi-agent system"""
    
    task_type = task.get('type', 'general_search')
    description = task.get('description', '')
    context = task.get('context', {})
    
    try:
        if 'agent_creation' in context:
            # Research for agent creation workflow
            agent_type = context.get('agent_type', '')
            result = await self.research_for_agent_creation(agent_type, context.get('capabilities', []))
        
        elif task_type in ['search_web', 'research', 'information_retrieval']:
            # Standard web search
            search_type = context.get('search_type', 'general')
            result = await self.perform_web_search(description, search_type)
        
        elif 'news' in description.lower():
            # News search
            result = await self.perform_web_search(description, 'news')
        
        elif any(word in description.lower() for word in ['tutorial', 'how to', 'guide']):
            # Tutorial search
            result = await self.perform_web_search(description, 'tutorial')
        
        else:
            # General search
            result = await self.perform_web_search(description, 'general')
        
        # Validate result advances original goal
        if await self.validates_goal_progress(task, result):
            self.complete_task(task, result)
        else:
            self.fail_task(task, "Search results don't advance original goal")
            
    except Exception as e:
        self.fail_task(task, f"Search failed: {str(e)}")
```

### Workspace Integration
```python
# Add to SearchAgent class
async def monitor_workspace(self):
    """Monitor workspace for search and research tasks"""
    while True:
        pending_tasks = self.scan_pending_tasks()
        
        for task_file in pending_tasks:
            task = self.load_task(task_file)
            
            # Check if this is a search/research task
            if await self.should_handle(task):
                if self.claim_task(task_file):
                    await self.process_task(task)
                    break
        
        await asyncio.sleep(1)

def scan_pending_tasks(self):
    """Scan workspace for relevant tasks"""
    pending_dir = os.path.join(self.workspace_path, "tasks", "pending")
    if not os.path.exists(pending_dir):
        return []
    
    return [
        os.path.join(pending_dir, f) 
        for f in os.listdir(pending_dir) 
        if f.endswith('.json')
    ]
```

## Key Changes Summary

1. **Inherit from BaseAgent**: Proper multi-agent architecture
2. **Add three-LLM system**: executor, evaluator, metacognition  
3. **Implement workspace monitoring**: Can claim and process tasks
4. **Fix search functionality**: Actually perform searches, don't just return metadata
5. **Add agent creation research**: Specialized research for building new agents
6. **Goal validation**: Ensure search results advance original objectives
7. **Autonomous operation**: Works without direct user interaction
8. **Atomic task claiming**: Participates in race-condition-free coordination

## Integration Points

- **TaskBreakdownAgent**: Receives research requests for agent creation
- **FileAgent**: Provides research results for code generation
- **TerminalAgent**: Receives documentation for tool installation
- **Multi-agent workflows**: Participates in complex task orchestration

The refactored SearchAgent will be a full participant in the autonomous multi-agent system, capable of providing research and information retrieval services while following all coordination protocols. 