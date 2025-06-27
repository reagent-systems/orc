# Voice and Video Streaming in ADK

ADK provides native support for real-time streaming conversations with models that support the Live API, enabling bidirectional voice and video interactions. This feature is particularly powerful for creating natural, conversational AI applications.

## Overview

ADK's streaming capabilities enable real-time, bidirectional audio and video communication between users and AI agents. Unlike traditional text-based interactions, streaming allows for:

- **Real-time voice conversations**: Natural speech input and audio responses
- **Video processing**: Camera input for visual understanding
- **Low-latency interactions**: Immediate response to user input
- **Interrupt handling**: Natural conversation flow with interruptions
- **Multimodal experiences**: Combining text, audio, and video seamlessly

## Supported Models

Currently, streaming is supported by models with Live API capability:

### Gemini 2.0 Flash Live Models
- **gemini-2.0-flash-exp**: Experimental live interaction model
- **gemini-2.0-flash-thinking-exp-1219**: Live model with reasoning capabilities

These models are specifically designed for real-time interactions and provide:
- Ultra-low latency responses
- Natural conversation flow
- Audio and video understanding
- Tool calling during streaming
- Multi-turn conversations

## Technical Requirements

### Environment Setup

#### SSL Configuration
For voice/video streaming, SSL certificates are required:

**Python:**
```bash
export SSL_CERT_FILE=$(python -m certifi)
```

**Windows PowerShell:**
```powershell
$env:SSL_CERT_FILE = python -m certifi
```

#### Model Authentication
Streaming requires proper model authentication:

**Google AI Studio:**
```bash
export GOOGLE_GENAI_USE_VERTEXAI=FALSE
export GOOGLE_API_KEY="your_api_key"
```

**Vertex AI:**
```bash
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT="your_project_id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

### Hardware Requirements
- **Microphone**: For audio input
- **Speakers/Headphones**: For audio output
- **Camera**: For video input (optional)
- **Stable Internet**: For real-time communication

## Setting Up Streaming Agents

### Basic Voice Agent

**Python:**
```python
from google.adk.agents import LlmAgent

# Create streaming-capable agent
voice_agent = LlmAgent(
    name="VoiceAssistant",
    model="gemini-2.0-flash-exp",
    description="A helpful voice assistant",
    instruction="You are a voice assistant. Keep responses conversational and natural.",
    # Note: Streaming is enabled automatically for Live API models
)
```

**Java:**
```java
import com.google.adk.agents.LlmAgent;

LlmAgent voiceAgent = LlmAgent.builder()
    .name("VoiceAssistant")
    .model("gemini-2.0-flash-exp")
    .description("A helpful voice assistant")
    .instruction("You are a voice assistant. Keep responses conversational and natural.")
    .build();
```

### Agent with Tools and Streaming

**Python:**
```python
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Implementation here
    return f"The weather in {city} is sunny and 72°F"

def set_reminder(message: str, time: str) -> str:
    """Set a reminder for the user."""
    # Implementation here
    return f"Reminder set: '{message}' for {time}"

streaming_agent = LlmAgent(
    name="StreamingAssistant",
    model="gemini-2.0-flash-exp",
    description="Voice assistant with weather and reminder capabilities",
    instruction="""You are a helpful voice assistant that can:
    - Check weather information
    - Set reminders for users
    - Have natural conversations
    
    Keep responses brief and conversational since this is voice interaction.""",
    tools=[get_weather, set_reminder]
)
```

## Running Streaming Sessions

### Using ADK Web UI

The easiest way to test streaming is through the ADK Web UI:

```bash
# Navigate to your agent directory
cd parent_folder/

# Launch development UI
adk web
```

**Web UI Features:**
- **Voice Input**: Click microphone button to start speaking
- **Camera Input**: Enable camera for video understanding
- **Real-time Response**: Immediate audio responses from agent
- **Interrupt Capability**: Stop agent mid-response to speak
- **Event Inspection**: View streaming events in real-time

### Programmatic Streaming

**Python:**
```python
from google.adk.runner import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import asyncio

async def streaming_example():
    # Set up services
    session_service = InMemorySessionService()
    runner = Runner(
        agent=streaming_agent,
        app_name="streaming_app",
        session_service=session_service
    )
    
    # Create session
    session = await session_service.create_session(
        app_name="streaming_app",
        user_id="user123"
    )
    
    # Start streaming conversation
    # Note: Actual audio/video handling depends on your application setup
    user_message = types.Content(
        role='user',
        parts=[types.Part(text="Hello, what's the weather like?")]
    )
    
    events = runner.run(
        user_id="user123",
        session_id=session.id,
        new_message=user_message
    )
    
    # Process streaming events
    for event in events:
        if hasattr(event, 'content') and event.content:
            print(f"Agent response: {event.content}")

# Run the example
asyncio.run(streaming_example())
```

## Streaming Features

### Real-Time Audio Processing

**Input Handling:**
- Continuous audio capture from microphone
- Automatic speech-to-text conversion
- Voice activity detection
- Background noise filtering

**Output Generation:**
- Real-time text-to-speech synthesis
- Natural voice characteristics
- Interruption handling
- Audio quality optimization

### Video Understanding

For models that support video input:

**Capabilities:**
- Real-time camera feed processing
- Object recognition and description
- Scene understanding
- Visual question answering
- Image-based tool calling

**Example Use Cases:**
- "What do you see in my room?"
- "Help me identify this plant"
- "Read the text on this document"
- "Count the objects on my desk"

### Multi-Modal Interactions

Streaming agents can process multiple input types simultaneously:

**Example Conversation:**
```
User: [Shows document on camera] "Can you read this and summarize it?"
Agent: [Processes video feed] "I can see a contract document. Let me read through it..."
User: [Interrupts] "Just focus on the payment terms"
Agent: "Looking at the payment section, I see..."
```

## Conversation Patterns

### Natural Interruptions

Streaming models handle interruptions gracefully:

```python
# Agent instruction for handling interruptions
instruction = """You are a voice assistant. When interrupted:
1. Stop speaking immediately
2. Acknowledge the interruption politely
3. Address the new topic or clarification
4. Keep responses concise since users can interrupt if they need more detail"""
```

### Turn-Taking

Implement natural conversation flow:

```python
instruction = """Maintain natural conversation patterns:
- Use brief acknowledgments ("I see", "Got it")
- Ask clarifying questions when needed
- Pause appropriately for user responses
- Signal when you're done speaking"""
```

### Context Continuity

Streaming conversations maintain context across interruptions:

```python
# Session state helps maintain context
session_state = {
    "current_topic": "weather_inquiry",
    "user_location": "San Francisco",
    "conversation_stage": "providing_forecast"
}
```

## Best Practices

### Agent Design for Streaming

#### 1. Conversational Instructions
```python
instruction = """You are a voice assistant optimized for spoken conversation:

SPEAKING STYLE:
- Use natural, conversational language
- Keep responses concise (2-3 sentences max initially)
- Use filler words and natural pauses
- Acknowledge interruptions gracefully

INTERACTION PATTERNS:
- Ask "Would you like me to continue?" for long responses
- Use confirmations: "Got it", "I understand"
- Signal completion: "Is there anything else?"

TECHNICAL CONSIDERATIONS:
- Remember this is voice - no markdown or formatting
- Spell out abbreviations and acronyms
- Use numbers appropriately (say "three" not "3")"""
```

#### 2. Tool Integration
```python
def weather_tool(city: str) -> str:
    """Get weather optimized for voice response."""
    # Get weather data
    weather_data = get_weather_data(city)
    
    # Format for speech
    return f"The current weather in {city} is {weather_data['condition']} with a temperature of {weather_data['temp']} degrees"
```

#### 3. Error Handling
```python
instruction += """
ERROR HANDLING:
- If you don't understand audio, say "I didn't catch that, could you repeat?"
- For unclear requests, ask specific clarifying questions
- If tools fail, explain simply what went wrong
"""
```

### Performance Optimization

#### 1. Response Timing
- Keep initial responses under 3 seconds
- Break long responses into chunks
- Use progressive disclosure

#### 2. Audio Quality
- Test in different acoustic environments
- Handle background noise gracefully
- Optimize for various microphone qualities

#### 3. Bandwidth Considerations
- Monitor streaming data usage
- Implement quality adaptation
- Handle connection interruptions

### User Experience

#### 1. Onboarding
```python
# Welcome message for new streaming sessions
welcome_instruction = """When starting a new voice conversation:
1. Greet the user warmly
2. Briefly explain your capabilities
3. Ask how you can help
4. Give examples if the user seems unsure"""
```

#### 2. Feedback Mechanisms
```python
# Implement audio cues for different states
def provide_audio_feedback(state):
    if state == "listening":
        return "I'm listening..."
    elif state == "processing":
        return "Let me think about that..."
    elif state == "tool_calling":
        return "Just checking that for you..."
```

## Advanced Streaming Patterns

### Multi-Agent Streaming

Streaming works with multi-agent systems:

```python
from google.adk.agents import LlmAgent, SequentialAgent

# Specialized streaming agents
weather_agent = LlmAgent(
    name="WeatherAgent",
    model="gemini-2.0-flash-exp",
    description="Weather information specialist",
    tools=[weather_tool]
)

calendar_agent = LlmAgent(
    name="CalendarAgent", 
    model="gemini-2.0-flash-exp",
    description="Calendar and scheduling specialist",
    tools=[calendar_tools]
)

# Coordinator for streaming
coordinator = LlmAgent(
    name="StreamingCoordinator",
    model="gemini-2.0-flash-exp",
    instruction="Route voice requests to appropriate specialists",
    sub_agents=[weather_agent, calendar_agent]
)
```

### Session Continuity

Maintain streaming context across sessions:

```python
# Resume streaming conversation
async def resume_streaming_session(user_id: str, session_id: str):
    session = await session_service.get_session(
        app_name="streaming_app",
        user_id=user_id, 
        session_id=session_id
    )
    
    # Check if previous conversation was interrupted
    if session.state.get("interrupted"):
        # Resume with context
        resume_message = "Welcome back! We were discussing..."
        # Continue streaming conversation
```

### Integration with Other Modalities

Combine streaming with other ADK features:

```python
# Agent that can handle both streaming and text
hybrid_agent = LlmAgent(
    name="HybridAgent",
    model="gemini-2.0-flash-exp",
    instruction="""You can handle both voice and text interactions:
    - For voice: Keep responses conversational and brief
    - For text: Provide more detailed, structured responses
    - Adapt your communication style to the input modality""",
    tools=[various_tools]
)
```

## Troubleshooting

### Common Issues

#### Audio Problems
- **No microphone access**: Check browser permissions
- **Poor audio quality**: Test microphone settings
- **Echo issues**: Use headphones or adjust audio levels

#### Streaming Interruptions
- **Connection drops**: Implement reconnection logic
- **High latency**: Check network conditions
- **Model timeouts**: Verify model availability

#### Model Compatibility
- **Wrong model type**: Ensure using Live API models
- **Authentication issues**: Verify API keys and credentials
- **Rate limiting**: Monitor API usage and implement backoff

### Debugging Streaming

```python
# Enable verbose logging for streaming
import logging
logging.basicConfig(level=logging.DEBUG)

# Monitor streaming events
def debug_streaming_events(events):
    for event in events:
        print(f"Event type: {type(event)}")
        print(f"Event content: {event}")
        if hasattr(event, 'metadata'):
            print(f"Event metadata: {event.metadata}")
```

Voice and video streaming in ADK opens up new possibilities for natural, immersive AI interactions. By understanding these capabilities and best practices, you can build agents that provide truly conversational experiences that feel more like talking to a helpful human than interacting with a computer. 