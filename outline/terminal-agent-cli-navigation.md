# Terminal Agent with CLI Navigation

## Overview
Advanced terminal agent capable of executing commands and navigating interactive CLI menus (Firebase, AWS CLI, npm, etc.)

## Core Capabilities
- Execute shell commands and capture output
- Navigate interactive CLI menus with arrow keys
- Handle text input prompts  
- Parse menu options and make intelligent selections
- Complete multi-step terminal workflows autonomously

## Architecture

### Base Agent Structure
```python
class TerminalAgent(BaseAgent):
    def __init__(self):
        super().__init__("TerminalAgent", [
            "command_execution", 
            "cli_navigation", 
            "interactive_terminals",
            "menu_parsing"
        ])
        
        self.terminal_session_tool = InteractiveTerminalTool()
        
    def get_executor_instruction(self) -> str:
        return """Execute terminal commands and navigate interactive CLI interfaces.
        
        Capabilities:
        - Run shell commands and capture output
        - Navigate interactive CLI menus (Firebase, AWS CLI, etc.)
        - Handle multi-step terminal workflows
        - Parse menu options and make selections
        - Input text when prompted
        - Handle arrow key navigation, enter, tab completion
        
        For interactive CLIs:
        1. Read and understand current menu state
        2. Identify available options
        3. Make appropriate selections based on task goals
        4. Handle text input prompts
        5. Navigate through multi-level menus
        6. Complete workflows step by step
        
        Always explain what menu options you see and why you're making specific choices."""
```

### Interactive Terminal Tool
```python
import pexpect
import time

class InteractiveTerminalTool:
    def __init__(self):
        self.active_sessions = {}
    
    async def start_interactive_session(self, command: str):
        """Start an interactive terminal session"""
        session_id = f"session_{uuid4().hex[:8]}"
        
        # Start the interactive process
        child = pexpect.spawn(command, timeout=30)
        child.setwinsize(24, 80)  # Standard terminal size
        
        session = TerminalSession(session_id, child)
        self.active_sessions[session_id] = session
        
        # Wait for initial output
        time.sleep(1)
        session.capture_current_state()
        
        return session
    
    def send_arrow_key(self, session: "TerminalSession", direction: str):
        """Send arrow key to navigate menus"""
        if direction == "UP":
            session.child.send('\x1b[A')  # Up arrow
        elif direction == "DOWN":
            session.child.send('\x1b[B')  # Down arrow
        elif direction == "LEFT":
            session.child.send('\x1b[D')  # Left arrow  
        elif direction == "RIGHT":
            session.child.send('\x1b[C')  # Right arrow
        
        time.sleep(0.5)
        session.capture_current_state()
```

### CLI State Analysis
```python
async def analyze_cli_state(self, output: str, goal: str):
    """Advanced CLI state analysis"""
    prompt = f"""
    Analyze this CLI interface output:
    
    {output}
    
    Goal: {goal}
    
    Identify:
    1. TYPE: [MENU|PROMPT|CONFIRMATION|ERROR|COMPLETION]
    2. OPTIONS: List all selectable options if this is a menu
    3. CURRENT_SELECTION: Which option is currently highlighted
    4. NEXT_ACTION: Best action to take toward the goal
    5. INPUT_NEEDED: If text input is required, what should be entered
    
    For menus, look for:
    - Arrow indicators (>, *, [x])
    - Numbered lists
    - Highlighted text
    - Selection brackets
    """
    
    analysis = await self.evaluator.process(prompt)
    return self.parse_cli_analysis(analysis)
```

## Supported CLI Patterns

### Firebase CLI
- Project selection menus
- Feature deployment options
- Hosting configuration
- Authentication flows

### AWS CLI  
- Service selection
- Configuration prompts
- Resource management
- Interactive setup

### Package Managers
- npm/yarn interactive commands
- Dependency selection
- Configuration wizards

### Git Interactive
- Interactive rebase
- Conflict resolution
- Branch selection

### Database CLIs
- Query builders
- Migration tools
- Connection setup

## Navigation Methods

### Menu Navigation
```python
async def navigate_cli_menu(self, command: str, goal: str):
    """Handle interactive CLI navigation"""
    session = await self.terminal_session_tool.start_interactive_session(command)
    
    while not session.is_complete():
        current_output = session.get_current_output()
        
        next_action = await self.executor.process(f"""
        CLI Navigation Task: {goal}
        Current terminal output: {current_output}
        
        Determine next action:
        ACTION: [SELECT_OPTION|INPUT_TEXT|ARROW_UP|ARROW_DOWN|ENTER|DONE]
        VALUE: [option_number|text_to_input|navigation_command]
        REASONING: [why this action]
        """)
        
        action_result = self.parse_and_execute_action(session, next_action)
        if action_result == "DONE":
            break
            
    return session.get_final_result()
```

### Input Handling
- Text prompts (credentials, paths, names)
- Arrow key navigation
- Tab completion
- Enter/escape handling
- Multi-character sequences

## Error Handling
- CLI command failures
- Menu parsing errors
- Session timeouts
- Unexpected prompts
- Recovery strategies

## Integration with Multi-Agent System

### Task Format
```json
{
    "description": "Deploy React app to Firebase hosting",
    "type": "deployment",
    "requirements": ["cli_navigation", "firebase"],
    "context": {
        "project_path": "./my-react-app",
        "hosting_config": "build folder",
        "cli_tool": "firebase"
    }
}
```

### Workflow Integration
- Works with FileAgent for project preparation
- Coordinates with SearchAgent for documentation lookup
- Handles deployment tasks from TaskBreakdownAgent

## Implementation Dependencies
- `pexpect` for interactive terminal control
- `ptyprocess` for pseudo-terminal handling
- Terminal escape sequence parsing
- CLI output pattern recognition

## Future Enhancements
- Screen scraping for complex UIs
- Machine learning for menu pattern recognition
- CLI tool fingerprinting
- Session recording and replay
- Parallel session management

This agent would provide autonomous CLI navigation capabilities for the multi-agent system, handling complex interactive terminal workflows without human intervention. 