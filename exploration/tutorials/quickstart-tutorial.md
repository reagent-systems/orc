# ADK Quickstart Tutorial

This tutorial will walk you through building your first AI agent using the Google Agent Development Kit (ADK). By the end, you'll have a functioning agent that can handle weather queries, manage a simple task list, and respond to natural language conversations.

## What You'll Build

We'll create a "Personal Assistant" agent that can:
- Provide weather information for different cities
- Manage a simple task list (add, view, complete tasks)
- Have natural conversations with users
- Handle multiple requests in a single conversation

## Prerequisites

Before starting, ensure you have:
- Python 3.9+ installed
- A Google AI Studio API key (free at [aistudio.google.com](https://aistudio.google.com))
- Basic familiarity with Python
- A terminal/command prompt

## Step 1: Environment Setup

### 1.1 Install ADK

```bash
# Create a new directory for your project
mkdir my-assistant-agent
cd my-assistant-agent

# Create and activate virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install ADK
pip install google-adk
```

### 1.2 Set Up Authentication

Create a `.env` file in your project directory:

```bash
# .env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual API key from Google AI Studio.

### 1.3 Verify Installation

```bash
# Check ADK installation
adk --version

# Should show version information
```

## Step 2: Create Your First Agent

### 2.1 Project Structure

Create the following structure:

```
my-assistant-agent/
├── .env
├── personal_assistant/
│   ├── __init__.py
│   └── agent.py
└── .venv/
```

### 2.2 Create the Agent Package

**Create `personal_assistant/__init__.py`:**

```python
# personal_assistant/__init__.py
from . import agent
```

**Create `personal_assistant/agent.py`:**

```python
# personal_assistant/agent.py
from google.adk.agents import LlmAgent
from typing import Dict, List
import json
import datetime

# Simple in-memory storage for tasks
tasks_storage = []

def get_weather(city: str) -> Dict[str, str]:
    """Get weather information for a city."""
    # This is a mock weather function - in real use, you'd call a weather API
    weather_data = {
        "new york": {"condition": "Sunny", "temp": "72°F", "humidity": "45%"},
        "london": {"condition": "Cloudy", "temp": "15°C", "humidity": "80%"},
        "tokyo": {"condition": "Rainy", "temp": "20°C", "humidity": "85%"},
        "san francisco": {"condition": "Foggy", "temp": "18°C", "humidity": "70%"},
        "sydney": {"condition": "Sunny", "temp": "25°C", "humidity": "55%"}
    }
    
    city_lower = city.lower()
    if city_lower in weather_data:
        data = weather_data[city_lower]
        return {
            "status": "success",
            "city": city.title(),
            "condition": data["condition"],
            "temperature": data["temp"],
            "humidity": data["humidity"],
            "message": f"The weather in {city.title()} is {data['condition']} with a temperature of {data['temp']} and humidity at {data['humidity']}."
        }
    else:
        return {
            "status": "error",
            "message": f"Sorry, I don't have weather information for {city}. I can provide weather for New York, London, Tokyo, San Francisco, or Sydney."
        }

def add_task(task_description: str, priority: str = "medium") -> Dict[str, str]:
    """Add a new task to the task list."""
    if not task_description.strip():
        return {
            "status": "error",
            "message": "Task description cannot be empty."
        }
    
    task = {
        "id": len(tasks_storage) + 1,
        "description": task_description.strip(),
        "priority": priority.lower(),
        "completed": False,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    tasks_storage.append(task)
    
    return {
        "status": "success",
        "message": f"Added task: '{task_description}' with {priority} priority.",
        "task_id": str(task["id"])
    }

def view_tasks(status: str = "all") -> Dict[str, str]:
    """View tasks from the task list."""
    if not tasks_storage:
        return {
            "status": "success",
            "message": "No tasks found. Your task list is empty."
        }
    
    if status == "completed":
        filtered_tasks = [task for task in tasks_storage if task["completed"]]
        title = "Completed Tasks"
    elif status == "pending":
        filtered_tasks = [task for task in tasks_storage if not task["completed"]]
        title = "Pending Tasks"
    else:
        filtered_tasks = tasks_storage
        title = "All Tasks"
    
    if not filtered_tasks:
        return {
            "status": "success",
            "message": f"No {status} tasks found."
        }
    
    task_list = f"\n{title}:\n" + "=" * (len(title) + 1) + "\n"
    for task in filtered_tasks:
        status_icon = "✓" if task["completed"] else "○"
        priority_indicator = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task["priority"], "⚪")
        task_list += f"{status_icon} [{task['id']}] {priority_indicator} {task['description']} (Created: {task['created_at']})\n"
    
    return {
        "status": "success",
        "message": task_list
    }

def complete_task(task_id: str) -> Dict[str, str]:
    """Mark a task as completed."""
    try:
        task_id_int = int(task_id)
    except ValueError:
        return {
            "status": "error",
            "message": "Task ID must be a number."
        }
    
    task = next((task for task in tasks_storage if task["id"] == task_id_int), None)
    
    if not task:
        return {
            "status": "error",
            "message": f"Task with ID {task_id} not found."
        }
    
    if task["completed"]:
        return {
            "status": "info",
            "message": f"Task '{task['description']}' is already completed."
        }
    
    task["completed"] = True
    task["completed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "status": "success",
        "message": f"✓ Completed task: '{task['description']}'"
    }

# Create the agent
root_agent = LlmAgent(
    name="PersonalAssistant",
    model="gemini-2.0-flash",
    description="A helpful personal assistant that can provide weather information and manage tasks",
    instruction="""You are a friendly and helpful personal assistant. You can:

1. **Weather Information**: Provide weather details for cities using the get_weather function
2. **Task Management**: Help users manage their tasks with these capabilities:
   - Add new tasks with add_task (specify priority: high, medium, or low)
   - View tasks with view_tasks (show all, completed, or pending tasks)
   - Mark tasks as complete with complete_task (using task ID)

**Conversation Style**:
- Be warm, friendly, and conversational
- Acknowledge user requests before performing actions
- Provide clear, helpful responses
- If something goes wrong, explain what happened and suggest alternatives
- Offer relevant follow-up suggestions

**Examples of how to help**:
- "I'll check the weather in Tokyo for you..."
- "Let me add that task to your list..."
- "Here are your current tasks..."
- "I've marked task #3 as completed!"

Always be proactive in offering help and making the interaction feel natural and supportive.""",
    tools=[get_weather, add_task, view_tasks, complete_task]
)
```

## Step 3: Test Your Agent

### 3.1 Run the Agent

```bash
# From your project directory (my-assistant-agent/)
adk web
```

This will start the ADK web interface at `http://localhost:8000`.

### 3.2 Test Conversations

Try these example conversations:

**Weather Queries:**
- "What's the weather like in New York?"
- "How's the weather in London today?"
- "Can you check the weather in Paris?" (This should show the error handling)

**Task Management:**
- "Add a task to buy groceries"
- "Add a high priority task to call the doctor"
- "Show me all my tasks"
- "Complete task number 1"
- "Show me only pending tasks"

**Natural Conversations:**
- "Hi, how can you help me?"
- "What can you do for me?"
- "I need help organizing my day"

## Step 4: Understand the Code

Let's break down the key components:

### 4.1 Tool Functions

Each tool function returns a dictionary with status information:

```python
def get_weather(city: str) -> Dict[str, str]:
    # Function logic here
    return {
        "status": "success",  # or "error"
        "message": "Human-readable response",
        # Additional data as needed
    }
```

### 4.2 Agent Configuration

```python
root_agent = LlmAgent(
    name="PersonalAssistant",           # Agent identifier
    model="gemini-2.0-flash",          # LLM model to use
    description="...",                  # Brief description of capabilities
    instruction="...",                  # Detailed behavior instructions
    tools=[func1, func2, ...]          # Available tools
)
```

### 4.3 Instruction Design

The instruction is crucial for agent behavior:
- **Role definition**: What the agent is
- **Capabilities**: What it can do
- **Conversation style**: How it should interact
- **Examples**: Show desired behavior patterns

## Step 5: Enhance Your Agent

### 5.1 Add Session State

Modify your agent to remember user preferences:

```python
# Add to agent.py
def set_preference(preference_key: str, preference_value: str) -> Dict[str, str]:
    """Set a user preference."""
    # In a real application, you'd save this to the session state
    # For now, we'll just acknowledge it
    return {
        "status": "success",
        "message": f"I've noted your preference: {preference_key} = {preference_value}"
    }

# Add to the tools list in root_agent
tools=[get_weather, add_task, view_tasks, complete_task, set_preference]
```

### 5.2 Add Error Handling

Improve the weather function with better error handling:

```python
def get_weather(city: str) -> Dict[str, str]:
    """Get weather information for a city."""
    if not city or not city.strip():
        return {
            "status": "error",
            "message": "Please specify a city name."
        }
    
    # Rest of the function...
```

### 5.3 Add Data Persistence

For a production agent, you'd want to persist task data:

```python
import json
import os

TASKS_FILE = "tasks.json"

def load_tasks():
    """Load tasks from file."""
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_tasks():
    """Save tasks to file."""
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks_storage, f, indent=2)

# Initialize tasks storage
tasks_storage = load_tasks()

# Modify your task functions to call save_tasks() after changes
```

## Step 6: Advanced Features

### 6.1 Multi-Agent System

Create a specialized weather agent:

```python
# Create a separate weather agent
weather_agent = LlmAgent(
    name="WeatherSpecialist",
    model="gemini-2.0-flash",
    description="Specialized weather information provider",
    instruction="You are a weather specialist. Provide detailed weather information and forecasts.",
    tools=[get_weather]
)

# Create a coordinator agent
from google.adk.tools import AgentTool

coordinator_agent = LlmAgent(
    name="CoordinatorAssistant",
    model="gemini-2.0-flash",
    description="Personal assistant that coordinates with specialists",
    instruction="""You coordinate different capabilities:
    - Use WeatherAgent for weather-related questions
    - Handle task management directly
    - Provide general assistance and conversation""",
    tools=[
        AgentTool(agent=weather_agent),
        add_task, view_tasks, complete_task
    ]
)
```

### 6.2 Add Streaming Support

For voice interactions, use a streaming-compatible model:

```python
voice_agent = LlmAgent(
    name="VoiceAssistant",
    model="gemini-2.0-flash-exp",  # Live API model
    description="Voice-enabled personal assistant",
    instruction="""You are a voice assistant. Keep responses:
    - Conversational and natural
    - Brief and to the point
    - Acknowledge actions clearly
    - Use spoken language patterns""",
    tools=[get_weather, add_task, view_tasks, complete_task]
)
```

## Step 7: Testing and Debugging

### 7.1 Add Logging

```python
import logging

# Add to the top of agent.py
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add logging to your functions
def add_task(task_description: str, priority: str = "medium") -> Dict[str, str]:
    logger.info(f"Adding task: {task_description} with priority: {priority}")
    # Rest of function...
```

### 7.2 Error Simulation

Test error handling by modifying functions to occasionally fail:

```python
import random

def get_weather(city: str) -> Dict[str, str]:
    # Simulate occasional API failures
    if random.random() < 0.1:  # 10% chance of failure
        return {
            "status": "error",
            "message": "Weather service temporarily unavailable. Please try again."
        }
    # Normal function logic...
```

## Step 8: Deployment Considerations

### 8.1 Environment Variables

For production, use environment variables for configuration:

```python
import os

# At the top of agent.py
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TASKS_FILE = os.getenv("TASKS_FILE", "tasks.json")
```

### 8.2 Database Integration

For production task storage:

```python
# Example with SQLite
import sqlite3

def init_database():
    conn = sqlite3.connect('tasks.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            priority TEXT DEFAULT 'medium',
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Call this when your agent starts
init_database()
```

## Next Steps

Congratulations! You've built a functional AI agent. Here are some ideas for further development:

### Immediate Enhancements
1. **Add more tools**: Calendar integration, email sending, web search
2. **Improve data persistence**: Use a proper database
3. **Add user authentication**: Multi-user support
4. **Enhance error handling**: More robust error recovery

### Advanced Features
1. **Multi-agent orchestration**: Specialized agents for different domains
2. **Streaming capabilities**: Voice and video interactions
3. **MCP integration**: Connect to external services
4. **Custom memory systems**: Long-term user preferences

### Production Deployment
1. **Containerization**: Docker deployment
2. **Cloud deployment**: Google Cloud, AWS, or Azure
3. **API integration**: Real weather APIs, calendar services
4. **Monitoring and logging**: Production observability

## Troubleshooting

### Common Issues

**Agent not found:**
- Ensure `__init__.py` exists and imports agent
- Check you're in the correct parent directory when running `adk web`

**API key errors:**
- Verify your `.env` file has the correct API key
- Check the environment variables are being loaded

**Tool function errors:**
- Ensure all tool functions return dictionaries
- Check function signatures match what the agent expects

**Model not responding:**
- Verify internet connection
- Check API quota and rate limits
- Try a different model if available

### Getting Help

- **Documentation**: https://google.github.io/adk-docs/
- **GitHub**: Report issues and find examples
- **Community**: Join discussions and forums

This tutorial has introduced you to the fundamentals of building AI agents with ADK. The framework provides powerful capabilities for creating sophisticated, multi-modal AI applications that can handle complex tasks and natural conversations. 