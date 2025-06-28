# Google Search Agent

A powerful AI agent built with Google's Agent Development Kit (ADK) that provides intelligent web search capabilities using Google's Search API.

## 🌟 Features

### Search Capabilities
- **General Web Search**: Comprehensive search with intelligent result summarization
- **News Search**: Recent news articles and current events
- **Academic Search**: Scholarly papers and research publications
- **Tutorial Search**: How-to guides and instructional content
- **Local Search**: Businesses and services in specific locations

### Intelligence Features
- **Smart Query Processing**: Optimizes search terms for better results
- **Result Summarization**: Provides key insights from search results
- **Source Verification**: Highlights credible and trustworthy sources
- **Contextual Understanding**: Adapts search strategy based on query type

## 🛠️ Prerequisites

- **Python 3.9+**
- **Google AI Studio API Key** or **Google Cloud Project** with Vertex AI
- **Google Custom Search Engine** (for web search functionality)
- **Google Search API Key** (Custom Search JSON API)

## 📋 Setup Instructions

### 1. Environment Setup

```bash
# Clone or navigate to the project directory
cd google-search-agent

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install ADK
pip install google-adk
```

### 2. Google Search API Configuration

#### Option A: Google Custom Search Engine (Recommended)

1. **Create a Custom Search Engine**:
   - Go to [Google Custom Search Engine](https://cse.google.com/cse/)
   - Click "Add" to create a new search engine
   - Enter a site to search (use `google.com` to search the entire web)
   - After creation, go to "Control Panel" → "Setup" → "Basics"
   - Toggle "Search the entire web" to ON
   - Note your **Search Engine ID**

2. **Get API Key**:
   - Go to [Google Cloud Console](https://console.developers.google.com/)
   - Create a new project or select existing one
   - Enable the **Custom Search JSON API**
   - Create credentials (API Key)
   - Note your **API Key**

#### Option B: Google Cloud Search API

1. **Set up Google Cloud Project**:
   - Create project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Custom Search JSON API
   - Create service account or API key
   - Configure authentication

### 3. Model Authentication

Choose your preferred model provider:

#### Google AI Studio (Easiest)
```bash
# Get API key from https://aistudio.google.com/
export GOOGLE_GENAI_USE_VERTEXAI=FALSE
export GOOGLE_API_KEY="your_google_ai_studio_key"
```

#### Google Cloud Vertex AI
```bash
# Set up Google Cloud authentication
gcloud auth application-default login
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="your_project_id" 
export GOOGLE_CLOUD_LOCATION="us-central1"
```

### 4. Search API Configuration

Create a `.env` file in the **project root** (not in the agent folder):

```bash
# Copy the template to project root  
cp .env.example .env

# Edit .env in project root with your keys
```

The `.env` file should contain:

```bash
# .env (in project root: /Users/thyfriendlyfox/Projects/orc/.env)
# Model Authentication (choose one)
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_google_ai_studio_key

# OR for Vertex AI:
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=your_project_id
# GOOGLE_CLOUD_LOCATION=us-central1

# Google Search Configuration
GOOGLE_SEARCH_API_KEY=your_custom_search_api_key
GOOGLE_SEARCH_ENGINE_ID=your_custom_search_engine_id

# Optional: Additional search settings
GOOGLE_SEARCH_MAX_RESULTS=10
```

## 🚀 Running the Agent

### Autonomous Mode (Multi-Agent System) ⭐ NEW

```bash
# Run from the google-search-agent directory
cd google-search-agent
python3 run_autonomous.py
```

The agent will monitor the **shared workspace** at `../workspace/tasks/pending/` and automatically claim search tasks.

**Important**: The workspace is created at the project root level (`/Users/thyfriendlyfox/Projects/orc/workspace/`) so all agents can share the same task queue.

### Testing Autonomous Mode

```bash
# From the google-search-agent directory:

# 1. Create test tasks (will be placed in ../workspace/tasks/pending/)
python3 create_test_task.py

# 2. Start autonomous agent (in another terminal)
python3 run_autonomous.py

# 3. Watch the agent process tasks automatically!
```

**Workspace Structure Created**:
```
/Users/thyfriendlyfox/Projects/orc/
├── .env                    # Shared environment config
├── workspace/              # Shared workspace for all agents
│   ├── tasks/
│   │   ├── pending/        # Tasks waiting to be claimed
│   │   ├── active/         # Tasks being processed
│   │   ├── completed/      # Finished tasks
│   │   └── failed/         # Failed tasks
│   ├── agents/             # Agent heartbeat files
│   ├── context/            # Shared context from completed tasks
│   └── results/            # Final deliverables
└── google-search-agent/    # This agent's code
```

### Traditional ADK Modes

#### Using ADK Web UI

```bash
# From the google-search-agent directory
adk web
```

Access the web interface at `http://localhost:8000`

#### Using Terminal Interface

```bash
# Run the agent in terminal mode
adk run search_agent
```

#### Using API Server

```bash
# Start API server for integration
adk api_server
```

## 💬 Example Conversations

### General Web Search
```
User: "What are the latest developments in artificial intelligence?"
Agent: I'll search for the latest information about artificial intelligence developments...
[Performs search and provides comprehensive summary with sources]
```

### News Search
```
User: "Find recent news about climate change"
Agent: I'll search for recent news about climate change from the last 7 days...
[Returns current news articles with summaries]
```

### Tutorial Search
```
User: "How do I learn Python programming?"
Agent: I'll search for tutorials and guides on how to learn Python programming...
[Finds step-by-step learning resources and guides]
```

### Academic Search
```
User: "Find research papers about machine learning in healthcare"
Agent: I'll search for academic papers and research on machine learning in healthcare...
[Returns scholarly articles and research papers]
```

### Local Search
```
User: "Find Italian restaurants in San Francisco"
Agent: I'll search for Italian restaurants in San Francisco...
[Returns local business results with details]
```

## 🔧 Configuration Options

### Search Parameters

You can customize search behavior by modifying the agent configuration:

```python
# In search_agent/agent.py
google_search = GoogleSearchTool(
    name="google_search",
    api_key="your_api_key",           # Optional: set directly
    search_engine_id="your_cse_id",   # Optional: set directly
    max_results=10,                   # Maximum results per search
    safe_search="moderate",           # Safe search level: off/moderate/strict
    language="en",                    # Search language
    country="us"                      # Search country/region
)
```

### Agent Behavior

Customize the agent's search strategy and response style:

```python
# Modify the instruction in root_agent to change behavior
instruction="""Your custom search agent instructions here..."""
```

## 🛡️ Security Best Practices

### API Key Management
- Never commit API keys to version control
- Use environment variables or secret management services
- Rotate API keys regularly
- Limit API key permissions to necessary scopes

### Rate Limiting
- Monitor API usage to avoid exceeding quotas
- Implement caching for frequently searched queries
- Consider using multiple API keys for high-volume applications

### Data Privacy
- Be aware of search query logging by Google
- Consider user privacy when logging search queries
- Implement data retention policies

## 📊 Usage Limits

### Google Custom Search API Limits
- **Free Tier**: 100 queries per day
- **Paid Tier**: Up to 10,000 queries per day
- **Rate Limit**: 10 queries per second

### Cost Considerations
- Free tier provides 100 searches/day at no cost
- Paid searches cost $5 per 1,000 queries (as of 2024)
- Monitor usage through Google Cloud Console

## 🔍 Advanced Features

### Custom Search Filters

Add custom search functions for specific domains:

```python
def search_specific_site(query: str, site: str) -> Dict[str, str]:
    """Search within a specific website."""
    site_query = f"{query} site:{site}"
    return {
        "status": "success",
        "query": site_query,
        "message": f"Searching for '{query}' on {site}..."
    }
```

### Multi-Language Search

```python
def search_in_language(query: str, language: str = "en") -> Dict[str, str]:
    """Search in a specific language."""
    return {
        "status": "success", 
        "query": query,
        "language": language,
        "message": f"Searching for '{query}' in {language}..."
    }
```

### Time-Based Search

```python
def search_recent(query: str, timeframe: str = "day") -> Dict[str, str]:
    """Search for recent results only."""
    time_query = f"{query} after:{timeframe}"
    return {
        "status": "success",
        "query": time_query,
        "timeframe": timeframe,
        "message": f"Searching for recent results about '{query}'..."
    }
```

## 🐛 Troubleshooting

### Common Issues

**"API key not found" errors:**
- Verify your `.env` file contains the correct Google Search API key
- Check that environment variables are loaded properly
- Ensure API key has proper permissions

**"Search engine not found" errors:**
- Verify your Custom Search Engine ID is correct
- Ensure the CSE is configured to search the entire web
- Check that the CSE is enabled and active

**"Quota exceeded" errors:**
- Check your daily quota usage in Google Cloud Console
- Consider upgrading to paid tier for higher limits
- Implement query caching to reduce API calls

**Model authentication errors:**
- Verify your Google AI Studio API key is valid
- For Vertex AI, ensure proper gcloud authentication
- Check that the correct environment variables are set

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add to your agent.py for detailed logging
logger = logging.getLogger(__name__)
logger.debug("Search query executed: %s", query)
```

## 🔗 Integration Examples

### Web Application Integration

```python
from flask import Flask, request, jsonify
from google.adk.runner import Runner
from google.adk.sessions import InMemorySessionService

app = Flask(__name__)
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="search_api",
    session_service=session_service
)

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    # Process search with agent
    # Return results as JSON
```

### Slack Bot Integration

```python
# Example Slack bot integration
from slack_bolt import App

@app.message("search")
def handle_search(message, say):
    query = message['text'].replace('search', '').strip()
    # Process with ADK agent
    # Send results to Slack
```

## 📈 Performance Optimization

### Caching Strategies
- Implement Redis or in-memory caching for frequent queries
- Cache search results for a reasonable time period
- Use query normalization to improve cache hit rates

### Async Processing
- Use async/await for better performance with multiple searches
- Implement background job processing for heavy search workloads
- Consider using task queues for high-volume applications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [ADK Official Docs](https://google.github.io/adk-docs/)
- **Google Search API**: [Custom Search JSON API](https://developers.google.com/custom-search/v1/overview)
- **Issues**: Report bugs and request features through GitHub issues
- **Community**: Join ADK community discussions

---

**Ready to search the web with AI?** 🔍✨

Start by setting up your API keys and running `adk web` to begin your intelligent search experience! 