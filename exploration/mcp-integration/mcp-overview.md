# Model Context Protocol (MCP) Integration

The Model Context Protocol (MCP) is an open standard that enables secure connections between AI applications and data sources. ADK provides first-class support for MCP, allowing agents to seamlessly integrate with a wide ecosystem of MCP-compatible tools and services.

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard designed to connect AI applications with data sources in a secure, controlled manner. MCP acts as a universal "adapter" that allows AI systems to access external tools, databases, APIs, and services through a standardized interface.

### Key Benefits of MCP

1. **Standardization**: Common protocol for tool integration across AI frameworks
2. **Security**: Secure, controlled access to external resources
3. **Interoperability**: Tools work across different AI applications
4. **Ecosystem**: Growing library of MCP-compatible servers and tools
5. **Flexibility**: Supports various data sources and capabilities

### MCP Architecture

```
AI Application (ADK Agent)
    ↓
MCP Client
    ↓ (MCP Protocol)
MCP Server
    ↓
External Resource (Database, API, File System, etc.)
```

## MCP in ADK

ADK provides native MCP integration through the `McpTool` class, which allows agents to connect to MCP servers and use their exposed tools seamlessly.

### Core Components

1. **McpTool**: ADK's MCP client implementation
2. **MCP Servers**: External services that expose tools via MCP
3. **Tool Registration**: Automatic discovery and registration of MCP tools
4. **Session Management**: Persistent connections to MCP servers

## Setting Up MCP Integration

### Installing MCP Dependencies

**Python:**
```bash
# Install MCP support (included in ADK)
pip install google-adk

# Install Node.js for MCP servers (if needed)
# Visit https://nodejs.org/
```

### Basic MCP Tool Usage

**Python:**
```python
from google.adk.agents import LlmAgent
from google.adk.tools import McpTool

# Create MCP tool connecting to a server
filesystem_mcp = McpTool(
    name="filesystem",
    command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
)

# Create agent with MCP tool
agent = LlmAgent(
    name="FileAgent",
    model="gemini-2.0-flash",
    description="Agent that can work with files",
    instruction="You can read, write, and manage files using the filesystem tool.",
    tools=[filesystem_mcp]
)
```

**Java:**
```java
import com.google.adk.agents.LlmAgent;
import com.google.adk.tools.McpTool;

// Create MCP tool
McpTool filesystemMcp = McpTool.builder()
    .name("filesystem")
    .command(List.of("npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"))
    .build();

// Create agent with MCP tool
LlmAgent agent = LlmAgent.builder()
    .name("FileAgent")
    .model("gemini-2.0-flash")
    .description("Agent that can work with files")
    .instruction("You can read, write, and manage files using the filesystem tool.")
    .tools(List.of(filesystemMcp))
    .build();
```

## Popular MCP Servers

### File System Server
Access local file systems securely.

**Setup:**
```python
filesystem_tool = McpTool(
    name="filesystem",
    command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
)
```

**Capabilities:**
- Read file contents
- Write files
- List directories
- Create/delete files and folders
- Search file contents

### SQLite Server
Connect to SQLite databases.

**Setup:**
```python
sqlite_tool = McpTool(
    name="sqlite",
    command=["npx", "-y", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"]
)
```

**Capabilities:**
- Execute SQL queries
- Schema inspection
- Table operations
- Data analysis

### Git Server
Interact with Git repositories.

**Setup:**
```python
git_tool = McpTool(
    name="git",
    command=["npx", "-y", "@modelcontextprotocol/server-git", "/path/to/repo"]
)
```

**Capabilities:**
- View repository status
- Read file history
- Branch operations
- Commit information

### Web Search Server
Perform web searches through MCP.

**Setup:**
```python
search_tool = McpTool(
    name="search",
    command=["npx", "-y", "@modelcontextprotocol/server-brave-search"],
    env={"BRAVE_API_KEY": "your_api_key"}
)
```

### Google Drive Server
Access Google Drive files and folders.

**Setup:**
```python
gdrive_tool = McpTool(
    name="gdrive",
    command=["npx", "-y", "@modelcontextprotocol/server-gdrive"],
    env={"GOOGLE_APPLICATION_CREDENTIALS": "/path/to/credentials.json"}
)
```

## Advanced MCP Usage

### Multiple MCP Servers

```python
from google.adk.agents import LlmAgent
from google.adk.tools import McpTool

# Set up multiple MCP tools
filesystem_tool = McpTool(
    name="filesystem",
    command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
)

database_tool = McpTool(
    name="database", 
    command=["npx", "-y", "@modelcontextprotocol/server-sqlite", "/data/app.db"]
)

web_tool = McpTool(
    name="web_search",
    command=["npx", "-y", "@modelcontextprotocol/server-brave-search"],
    env={"BRAVE_API_KEY": "your_api_key"}
)

# Create agent with multiple MCP capabilities
multi_tool_agent = LlmAgent(
    name="MultiToolAgent",
    model="gemini-2.0-flash",
    description="Agent with file, database, and web search capabilities",
    instruction="""You have access to:
    - filesystem: Read/write files in /workspace
    - database: Query SQLite database
    - web_search: Search the internet for information
    
    Use these tools to help users with complex tasks requiring multiple data sources.""",
    tools=[filesystem_tool, database_tool, web_tool]
)
```

### Environment Configuration

```python
# MCP server with environment variables
mcp_tool = McpTool(
    name="custom_server",
    command=["python", "/path/to/custom_mcp_server.py"],
    env={
        "API_KEY": "your_api_key",
        "DATABASE_URL": "postgresql://user:pass@localhost/db",
        "LOG_LEVEL": "DEBUG"
    }
)
```

### Custom MCP Server Arguments

```python
# MCP server with specific arguments
weather_tool = McpTool(
    name="weather",
    command=[
        "python", 
        "/path/to/weather_server.py",
        "--api-key", "your_weather_api_key",
        "--default-units", "metric",
        "--cache-duration", "300"
    ]
)
```

## Building Custom MCP Servers

While ADK primarily consumes MCP servers, you can build custom MCP servers for specialized integrations.

### Python MCP Server Template

```python
#!/usr/bin/env python3
"""
Custom MCP Server example
"""
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Create server instance
server = Server("custom-server")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="custom_function",
            description="Performs a custom operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input parameter"}
                },
                "required": ["input"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "custom_function":
        input_value = arguments.get("input", "")
        result = f"Processed: {input_value}"
        return [TextContent(type="text", text=result)]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

### Using Custom Server in ADK

```python
# Use the custom MCP server
custom_tool = McpTool(
    name="custom",
    command=["python", "/path/to/custom_server.py"]
)

agent = LlmAgent(
    name="CustomAgent",
    model="gemini-2.0-flash",
    tools=[custom_tool]
)
```

## MCP Tool Discovery and Introspection

### Tool Discovery
MCP tools are automatically discovered and registered:

```python
# Create MCP tool
mcp_tool = McpTool(
    name="filesystem",
    command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
)

# Tools are automatically discovered when the agent runs
# The agent will see available tools like:
# - read_file
# - write_file
# - list_directory
# - create_directory
# etc.
```

### Inspecting Available Tools

```python
# You can inspect what tools are available from an MCP server
# This happens automatically during agent execution
agent = LlmAgent(
    name="FileAgent",
    model="gemini-2.0-flash",
    instruction="""You have access to filesystem tools. 
    When a user asks what you can do, list the available file operations.""",
    tools=[filesystem_tool]
)
```

## Integration Patterns

### Data Analysis Pipeline

```python
# Combine MCP tools for data analysis
from google.adk.agents import SequentialAgent, LlmAgent

# Data extraction agent
extractor = LlmAgent(
    name="DataExtractor",
    model="gemini-2.0-flash",
    instruction="Extract data from database and save to files",
    tools=[database_tool, filesystem_tool],
    output_key="extracted_data"
)

# Data analysis agent
analyzer = LlmAgent(
    name="DataAnalyzer", 
    model="gemini-2.0-flash",
    instruction="Analyze the extracted data and generate insights",
    tools=[filesystem_tool],
    output_key="analysis_results"
)

# Report generator
reporter = LlmAgent(
    name="ReportGenerator",
    model="gemini-2.0-flash", 
    instruction="Generate report from analysis results",
    tools=[filesystem_tool]
)

# Complete pipeline
analysis_pipeline = SequentialAgent(
    name="DataAnalysisPipeline",
    sub_agents=[extractor, analyzer, reporter]
)
```

### Multi-Source Research

```python
# Research agent using multiple MCP sources
research_agent = LlmAgent(
    name="ResearchAgent",
    model="gemini-2.0-flash",
    description="Comprehensive research assistant",
    instruction="""You are a research assistant with access to:
    - Web search for current information
    - Local file system for documents and notes
    - Database for structured data
    
    For research tasks:
    1. Search the web for current information
    2. Check local files for existing research
    3. Query database for relevant data
    4. Synthesize findings into comprehensive reports
    5. Save results for future reference""",
    tools=[web_search_tool, filesystem_tool, database_tool]
)
```

## Security and Best Practices

### Server Isolation
```python
# Use restricted directory access
secure_fs_tool = McpTool(
    name="secure_filesystem",
    command=["npx", "-y", "@modelcontextprotocol/server-filesystem", "/secure/workspace"],
    # Server only has access to /secure/workspace and subdirectories
)
```

### Environment Variable Management
```python
import os

# Use environment variables for sensitive data
secure_tool = McpTool(
    name="api_tool",
    command=["python", "/path/to/api_server.py"],
    env={
        "API_KEY": os.getenv("SECURE_API_KEY"),
        "DATABASE_URL": os.getenv("DATABASE_URL")
    }
)
```

### Error Handling
```python
# Robust agent with MCP error handling
resilient_agent = LlmAgent(
    name="ResilientAgent",
    model="gemini-2.0-flash",
    instruction="""You have access to external tools via MCP.
    
    If a tool fails:
    1. Acknowledge the error to the user
    2. Try alternative approaches if available
    3. Provide partial results when possible
    4. Suggest manual alternatives when tools are unavailable""",
    tools=[mcp_tools]
)
```

## Troubleshooting MCP Integration

### Common Issues

#### Server Startup Failures
```python
# Debug MCP server startup
import logging
logging.basicConfig(level=logging.DEBUG)

# Check if Node.js and packages are available
mcp_tool = McpTool(
    name="debug_server",
    command=["npx", "--version"]  # Test command first
)
```

#### Permission Issues
```bash
# Ensure proper permissions for MCP servers
chmod +x /path/to/mcp/server
# Or use absolute paths to avoid PATH issues
```

#### Environment Problems
```python
# Verify environment setup
mcp_tool = McpTool(
    name="env_test",
    command=["env"],  # List environment variables
    env={"TEST_VAR": "test_value"}
)
```

### Debugging MCP Communication

```python
# Enable MCP debugging
import os
os.environ["MCP_DEBUG"] = "1"

# Create agent with verbose MCP logging
debug_agent = LlmAgent(
    name="DebugAgent",
    model="gemini-2.0-flash",
    instruction="Test MCP tool communication",
    tools=[mcp_tool]
)
```

## MCP Ecosystem

### Available MCP Servers
- **@modelcontextprotocol/server-filesystem**: File system operations
- **@modelcontextprotocol/server-sqlite**: SQLite database access
- **@modelcontextprotocol/server-git**: Git repository operations
- **@modelcontextprotocol/server-brave-search**: Web search
- **@modelcontextprotocol/server-gdrive**: Google Drive integration
- **@modelcontextprotocol/server-github**: GitHub API integration
- **@modelcontextprotocol/server-postgres**: PostgreSQL database access

### Community Servers
The MCP ecosystem is growing rapidly with community-contributed servers for various services and APIs.

### Building Your Own
Consider contributing MCP servers for:
- Internal APIs and databases
- Specialized data sources
- Custom business logic
- Third-party service integrations

MCP integration in ADK opens up a vast ecosystem of tools and data sources, enabling agents to work with diverse external systems through a standardized, secure protocol. This makes ADK agents more powerful and versatile while maintaining security and interoperability. 