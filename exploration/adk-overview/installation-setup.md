# Installation and Setup Guide

This guide walks you through setting up the Google Agent Development Kit (ADK) for development on your local machine.

## Prerequisites

### System Requirements
- **Python**: 3.9+ (for Python ADK)
- **Java**: 17+ (for Java ADK)
- **Operating System**: macOS, Linux, or Windows
- **Terminal/Command Line**: Access to terminal or command prompt

### Development Environment
- **IDE**: VS Code, PyCharm, IntelliJ IDEA, or similar
- **Git**: For version control (optional but recommended)
- **Node.js**: Required for some MCP tools (optional)

## Python Installation

### 1. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows CMD:
.venv\Scripts\activate.bat

# Windows PowerShell:
.venv\Scripts\Activate.ps1
```

### 2. Install ADK

```bash
pip install google-adk
```

### 3. Verify Installation

```bash
# Check if ADK is installed
adk --version

# Verify command is available
which adk
```

## Java Installation

### 1. Project Structure

Create a Maven project with this structure:

```
project_folder/
├── pom.xml
└── src/
    └── main/
        └── java/
            └── agents/
                └── your_package/
```

### 2. Maven Configuration

Add to your `pom.xml`:

```xml
<dependency>
    <groupId>com.google.adk</groupId>
    <artifactId>google-adk</artifactId>
    <version>0.1.0</version>
</dependency>
```

### 3. Gradle Configuration (Alternative)

Add to your `build.gradle`:

```gradle
dependencies {
    implementation 'com.google.adk:google-adk:0.1.0'
}
```

## Model Authentication Setup

Choose your preferred model provider and set up authentication:

### Option 1: Google AI Studio (Recommended for Development)

1. **Get API Key**:
   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Create or sign in to your account
   - Generate an API key

2. **Set Environment Variables** (Python):
   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=FALSE
   export GOOGLE_API_KEY="your_api_key_here"
   ```

3. **Create .env file** (Python projects):
   ```
   GOOGLE_GENAI_USE_VERTEXAI=FALSE
   GOOGLE_API_KEY=your_api_key_here
   ```

### Option 2: Google Cloud Vertex AI (Recommended for Production)

1. **Set up Google Cloud**:
   - Create a [Google Cloud project](https://cloud.google.com/)
   - Set up the [gcloud CLI](https://cloud.google.com/sdk/docs/install)
   - Enable the Vertex AI API

2. **Authenticate**:
   ```bash
   gcloud auth application-default login
   ```

3. **Set Environment Variables**:
   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=TRUE
   export GOOGLE_CLOUD_PROJECT="your_project_id"
   export GOOGLE_CLOUD_LOCATION="us-central1"
   ```

## Quick Project Setup

### Python Project Structure

```
parent_folder/
    your_agent/
        __init__.py
        agent.py
        .env
```

### Create Your First Agent

**1. Create `__init__.py`**:
```python
from . import agent
```

**2. Create `agent.py`**:
```python
from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """Get weather for a city."""
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": "Sunny, 25°C (77°F)"
        }
    else:
        return {
            "status": "error", 
            "error_message": f"Weather for '{city}' not available."
        }

root_agent = Agent(
    name="weather_agent",
    model="gemini-2.0-flash",
    description="Agent to answer weather questions",
    instruction="You help users with weather information",
    tools=[get_weather],
)
```

### Java Agent Example

```java
package agents.example;

import com.google.adk.agents.LlmAgent;
import com.google.adk.tools.FunctionTool;
import java.util.Map;

public class WeatherAgent {
    public static BaseAgent ROOT_AGENT = initAgent();

    public static BaseAgent initAgent() {
        return LlmAgent.builder()
            .name("weather_agent")
            .model("gemini-2.0-flash")
            .description("Weather information agent")
            .instruction("Help users with weather information")
            .tools(FunctionTool.create(WeatherAgent.class, "getWeather"))
            .build();
    }

    public static Map<String, String> getWeather(String city) {
        if ("new york".equalsIgnoreCase(city)) {
            return Map.of("status", "success", 
                         "report", "Sunny, 25°C");
        }
        return Map.of("status", "error", 
                     "error", "Weather not available");
    }
}
```

## Running Your Agent

### Using ADK Web UI (Development)

```bash
# Navigate to parent directory of your agent folder
cd parent_folder/

# Launch development UI
adk web
```

Access at `http://localhost:8000` in your browser.

### Using Terminal Interface

```bash
# Run agent in terminal
adk run your_agent
```

### Using API Server

```bash
# Create local API server for testing
adk api_server
```

## Testing Your Setup

### Example Prompts
Try these prompts with your weather agent:
- "What's the weather in New York?"
- "How's the weather in Paris?"
- "Tell me about the weather in London"

### Expected Behavior
- New York queries should return sunny weather
- Other cities should return "not available" message
- The agent should use the `get_weather` tool appropriately

## Development Tools

### ADK CLI Commands

```bash
# Available commands
adk --help

# Run agent
adk run <agent_path>

# Launch web UI
adk web

# Start API server
adk api_server

# Run tests
adk test

# Create new project
adk create <project_name>
```

### Development UI Features
- **Agent Selection**: Choose from available agents
- **Chat Interface**: Interactive conversation
- **Event Inspector**: View function calls and responses
- **Trace Viewer**: Monitor execution performance
- **Voice/Video**: Streaming capabilities (with compatible models)

## Optional Dependencies

### For MCP (Model Context Protocol) Tools

```bash
# Install Node.js for MCP servers
# Visit https://nodejs.org/

# Verify installation
npx --version
```

### For Streaming Capabilities

Streaming requires models that support the Live API:
- Gemini 2.0 Flash Live models
- Set `SSL_CERT_FILE` for voice/video:

```bash
export SSL_CERT_FILE=$(python -m certifi)
```

### For Advanced Features

```bash
# Additional packages for specific features
pip install google-adk[vertexai]     # Vertex AI integration
pip install google-adk[agent_engine] # Agent Engine support
pip install litellm                  # Multi-model support
```

## Troubleshooting

### Common Issues

**Python Path Issues (Windows)**:
- Use `adk web --no-reload` if getting transport errors

**Model Authentication**:
- Verify API key is correctly set
- Check environment variables are loaded
- Ensure model name is correct

**Agent Not Found**:
- Verify `__init__.py` exists and imports agent
- Check you're in the correct parent directory
- Ensure agent has `root_agent` variable

**Java Compilation**:
- Verify Java 17+ is installed
- Check Maven/Gradle dependencies
- Ensure correct package structure

### Getting Help

- **Documentation**: https://google.github.io/adk-docs/
- **GitHub Issues**: Report bugs and get support
- **Community**: Join discussions and forums
- **Examples**: Check official sample projects

## Next Steps

1. **Follow Tutorials**: Try the quickstart tutorial
2. **Explore Agent Types**: Learn about different agent types
3. **Add Tools**: Integrate external APIs and services
4. **Multi-Agent Systems**: Build collaborative agent networks
5. **Deploy**: Move to production with Agent Engine

Your ADK development environment is now ready! Start building your first agent to explore the framework's capabilities. 