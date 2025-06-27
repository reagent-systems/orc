# Session Management in ADK

Sessions in ADK are the fundamental unit for tracking individual conversations between users and agents. Think of a Session as a "conversation thread" - it maintains context, history, and state for a specific interaction sequence.

## Overview

A **Session** is the ADK object designed to track and manage individual conversation threads. Just as you wouldn't start every text message from scratch, agents need context regarding ongoing interactions. Sessions provide this continuity by maintaining:

- **Conversation history**: All interactions and events
- **Session state**: Temporary data relevant to the current conversation  
- **Context management**: Seamless continuation across multiple turns
- **User association**: Linking conversations to specific users

## The Session Object

When a user starts interacting with your agent, the `SessionService` creates a `Session` object (`google.adk.sessions.Session`). This object acts as the container for everything related to that specific chat thread.

### Key Properties

#### Identification
- **`id`**: Unique identifier for this specific conversation thread
- **`app_name`**: Identifies which agent application this conversation belongs to
- **`user_id`**: Links the conversation to a particular user

#### Content
- **`events`**: Chronological sequence of all interactions (Event objects)
- **`state`**: Temporary data storage for this conversation (key-value pairs)
- **`last_update_time`**: Timestamp of the last interaction

### Example: Examining Session Properties

**Python:**
```python
from google.adk.sessions import InMemorySessionService

# Create a session service
temp_service = InMemorySessionService()

# Create a session with initial state
example_session = await temp_service.create_session(
    app_name="my_app",
    user_id="example_user",
    state={"initial_key": "initial_value"}
)

# Examine session properties
print(f"Session ID: {example_session.id}")
print(f"App Name: {example_session.app_name}")
print(f"User ID: {example_session.user_id}")
print(f"State: {example_session.state}")
print(f"Events: {example_session.events}")
print(f"Last Update: {example_session.last_update_time}")
```

**Java:**
```java
import com.google.adk.sessions.InMemorySessionService;
import com.google.adk.sessions.Session;

String sessionId = "123";
String appName = "example-app";
String userId = "example-user";
ConcurrentMap<String, Object> initialState = new ConcurrentHashMap<>();
initialState.put("initial_key", "initial_value");

InMemorySessionService sessionService = new InMemorySessionService();

// Create session
Session session = sessionService.createSession(
    appName, userId, initialState, Optional.of(sessionId)
).blockingGet();

// Examine properties
System.out.println("Session ID: " + session.id());
System.out.println("App Name: " + session.appName());
System.out.println("User ID: " + session.userId());
System.out.println("State: " + session.state());
```

## SessionService: Managing Session Lifecycle

You don't typically create or manage `Session` objects directly. Instead, you use a **`SessionService`** - the central manager responsible for the entire lifecycle of conversation sessions.

### Core Responsibilities

1. **Starting New Conversations**: Creating fresh Session objects
2. **Resuming Existing Conversations**: Retrieving specific sessions by ID
3. **Saving Progress**: Appending new interactions (Events) to session history
4. **Listing Conversations**: Finding active sessions for users and applications
5. **Cleaning Up**: Deleting sessions when no longer needed

### SessionService Implementations

ADK provides different implementations for various storage needs:

#### 1. InMemorySessionService
**Best for**: Development, testing, examples

**Characteristics:**
- Stores all data in application memory
- **No persistence**: Data lost on application restart
- No external dependencies required
- Fast and simple

**Python:**
```python
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
```

**Java:**
```java
import com.google.adk.sessions.InMemorySessionService;

InMemorySessionService sessionService = new InMemorySessionService();
```

#### 2. VertexAiSessionService
**Best for**: Production applications on Google Cloud

**Characteristics:**
- Uses Google Cloud Vertex AI infrastructure
- **Persistent**: Reliable, scalable data management
- Integrates with Vertex AI Agent Engine
- Requires Google Cloud setup

**Requirements:**
- Google Cloud project
- Vertex AI API enabled
- Proper authentication (ADC)
- Storage bucket configuration
- Reasoning Engine resource

**Python:**
```python
from google.adk.sessions import VertexAiSessionService

PROJECT_ID = "your-gcp-project-id"
LOCATION = "us-central1"
REASONING_ENGINE_APP_NAME = "projects/your-project/locations/us-central1/reasoningEngines/your-engine-id"

session_service = VertexAiSessionService(
    project=PROJECT_ID, 
    location=LOCATION
)
```

**Java:**
```java
import com.google.adk.sessions.VertexAiSessionService;

String reasoningEngineAppName = "123456789";
String userId = "u_123";
ConcurrentMap<String, Object> initialState = new ConcurrentHashMap<>();

VertexAiSessionService sessionService = new VertexAiSessionService();
Session session = sessionService.createSession(
    reasoningEngineAppName, userId, initialState, Optional.of(sessionId)
).blockingGet();
```

#### 3. DatabaseSessionService (Python Only)
**Best for**: Self-managed persistent storage

**Characteristics:**
- Connects to relational databases (PostgreSQL, MySQL, SQLite)
- **Persistent**: Data survives application restarts
- Self-managed infrastructure
- Configurable database backends

**Python:**
```python
from google.adk.sessions import DatabaseSessionService

# Example using SQLite
db_url = "sqlite:///./my_agent_data.db"
session_service = DatabaseSessionService(db_url=db_url)
```

## Session Lifecycle

Understanding the session lifecycle helps you design better agent interactions:

### 1. Session Creation/Retrieval
```python
# Create new session
session = await session_service.create_session(
    app_name="my_app",
    user_id="user123"
)

# Or retrieve existing session
session = await session_service.get_session(
    app_name="my_app",
    user_id="user123",
    session_id="existing_session_id"
)
```

### 2. Agent Processing
The agent receives user input and processes it using:
- Current session state
- Conversation history (events)
- Available tools and capabilities

### 3. Response Generation
Agent generates response and potentially updates session state:
```python
# State updates happen via events
from google.adk.events import Event, EventActions

# Create event with state changes
state_changes = {'user_preference': 'dark_mode'}
actions = EventActions(state_delta=state_changes)
event = Event(
    invocation_id="inv_123",
    author="agent",
    actions=actions
)
```

### 4. Session Update
```python
# Append event to session
await session_service.append_event(session, event)
```

### 5. Cleanup
```python
# Delete session when conversation is complete
await session_service.delete_session(
    app_name="my_app",
    user_id="user123",
    session_id=session.id
)
```

## Working with Sessions

### Creating Sessions with Initial State
```python
# Python
session = await session_service.create_session(
    app_name="shopping_assistant",
    user_id="customer_456",
    state={
        "cart_items": [],
        "preferred_currency": "USD",
        "customer_tier": "premium"
    }
)
```

### Listing User Sessions
```python
# Get all sessions for a user
sessions = await session_service.list_sessions(
    app_name="my_app",
    user_id="user123"
)
```

### Session State Management
```python
# Reading state
current_cart = session.state.get("cart_items", [])

# Updating state (recommended way)
await session_service.update_session_state(
    session_id=session.id,
    updates={"cart_items": updated_cart}
)
```

## Integration with ADK Runner

The `Runner` automatically manages sessions during agent execution:

### Setting Up Runner with SessionService
```python
from google.adk.runner import Runner
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()

runner = Runner(
    agent=root_agent,
    app_name="my_app",
    session_service=session_service
)
```

### Running with Session Context
```python
from google.genai import types

# Create or get session
session = await session_service.create_session(
    app_name="my_app",
    user_id="user123"
)

# Prepare user message
user_message = types.Content(
    role='user', 
    parts=[types.Part(text="Hello, how can you help me?")]
)

# Run agent with session context
events = runner.run(
    user_id="user123",
    session_id=session.id,
    new_message=user_message
)

# Process events
for event in events:
    if event.is_final_response():
        print(f"Agent: {event.content.parts[0].text}")
```

## Best Practices

### Session Design
1. **Meaningful IDs**: Use descriptive app names and user IDs
2. **State Organization**: Use consistent key naming conventions
3. **Cleanup Strategy**: Implement session cleanup policies
4. **Error Handling**: Handle session creation and retrieval failures

### State Management
1. **Key Prefixes**: Organize state with prefixes (`user.`, `app.`, `tool.`)
2. **Serializable Data**: Ensure all state values are serializable
3. **Size Limits**: Be mindful of state size for performance
4. **Atomic Updates**: Use official update methods for consistency

### Performance Considerations
1. **Service Selection**: Choose appropriate SessionService for your use case
2. **Session Cleanup**: Regularly clean up old sessions
3. **State Size**: Monitor and limit session state size
4. **Concurrent Access**: Handle concurrent session access properly

### Security
1. **User Isolation**: Ensure users can only access their own sessions
2. **Data Encryption**: Use encrypted storage for sensitive data
3. **Access Control**: Implement proper authentication and authorization
4. **Audit Logging**: Track session access and modifications

## Common Patterns

### Multi-Turn Conversations
```python
# Session maintains context across turns
session = await session_service.create_session(
    app_name="assistant",
    user_id="user123",
    state={"conversation_context": "customer_support"}
)

# Turn 1
events1 = runner.run(user_id="user123", session_id=session.id, 
                    new_message=types.Content(...))

# Turn 2 - session remembers previous context
events2 = runner.run(user_id="user123", session_id=session.id, 
                    new_message=types.Content(...))
```

### Session Branching
```python
# Create new session based on existing one
base_session = await session_service.get_session(...)
new_session = await session_service.create_session(
    app_name="my_app",
    user_id="user123",
    state=base_session.state.copy()  # Start with same state
)
```

### Session Templates
```python
# Create sessions with predefined templates
CUSTOMER_SUPPORT_TEMPLATE = {
    "conversation_type": "support",
    "priority": "normal",
    "department": "general"
}

session = await session_service.create_session(
    app_name="support_app",
    user_id="customer_id",
    state=CUSTOMER_SUPPORT_TEMPLATE
)
```

Sessions provide the foundation for building stateful, context-aware agents that can maintain meaningful conversations across multiple interactions. By understanding session management, you can create agents that feel more natural and helpful to users. 