# Python SDK Reference

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/python

Complete API reference for the Python Agent SDK.

## Choosing Between `query()` and `ClaudeSDKClient`

| Feature | `query()` | `ClaudeSDKClient` |
|:--------|:----------|:------------------|
| **Session** | Creates new session each time | Reuses same session |
| **Conversation** | Single exchange | Multiple exchanges |
| **Hooks** | Not supported | Supported |
| **Custom Tools** | Not supported | Supported |
| **Continue Chat** | New session each time | Maintains conversation |

## Functions

### `query()`

Creates a new session for each interaction:

```python
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None
) -> AsyncIterator[Message]
```

### `tool()`

Decorator for defining MCP tools:

```python
from claude_agent_sdk import tool

@tool("greet", "Greet a user", {"name": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{
            "type": "text",
            "text": f"Hello, {args['name']}!"
        }]
    }
```

### `create_sdk_mcp_server()`

Create an in-process MCP server:

```python
from claude_agent_sdk import create_sdk_mcp_server

calculator = create_sdk_mcp_server(
    name="calculator",
    version="1.0.0",
    tools=[add, multiply]
)
```

## Classes

### `ClaudeSDKClient`

Maintains a conversation session across multiple exchanges:

```python
async with ClaudeSDKClient() as client:
    await client.query("What's the capital of France?")
    async for message in client.receive_response():
        print(message)

    # Follow-up - Claude remembers context
    await client.query("What's the population of that city?")
    async for message in client.receive_response():
        print(message)
```

### `ClaudeAgentOptions`

Configuration dataclass:

```python
@dataclass
class ClaudeAgentOptions:
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    resume: str | None = None
    max_turns: int | None = None
    model: str | None = None
    cwd: str | Path | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[SettingSource] | None = None
```

### `AgentDefinition`

Configuration for subagents:

```python
@dataclass
class AgentDefinition:
    description: str
    prompt: str
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
```

## Message Types

```python
Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage
```

### `ResultMessage`

```python
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    result: str | None = None
```

## Permission Modes

```python
PermissionMode = Literal[
    "default",           # Standard permission behavior
    "acceptEdits",       # Auto-accept file edits
    "plan",              # Planning mode - no execution
    "bypassPermissions"  # Bypass all permission checks
]
```

## Built-in Tools

### AskUserQuestion

Ask the user clarifying questions with structured multiple-choice options.

**Input Schema:**

```python
{
    "questions": [  # 1-4 questions
        {
            "question": str,      # The complete question (ends with ?)
            "header": str,        # Short label, max 12 chars (e.g., "Tone", "Format")
            "options": [          # 2-4 options
                {
                    "label": str,       # Display text, 1-5 words
                    "description": str  # Explanation of this option
                }
            ],
            "multiSelect": bool   # True to allow multiple selections
        }
    ]
}
```

**Example:**

```python
# Ask about agent tone and output format
AskUserQuestion(questions=[
    {
        "question": "What tone should the agent use?",
        "header": "Tone",
        "options": [
            {"label": "Professional", "description": "Formal, business-appropriate"},
            {"label": "Casual", "description": "Friendly, conversational"},
            {"label": "Technical", "description": "Precise, developer-focused"}
        ],
        "multiSelect": False
    },
    {
        "question": "What output formats do you need?",
        "header": "Format",
        "options": [
            {"label": "Markdown", "description": "Formatted text with headers"},
            {"label": "JSON", "description": "Structured data output"},
            {"label": "Plain text", "description": "Simple unformatted text"}
        ],
        "multiSelect": True  # Allow multiple selections
    }
])
```

**Notes:**
- Users can always select "Other" to provide custom input
- Put recommended options first with "(Recommended)" in the label
- Use `multiSelect: True` when choices aren't mutually exclusive

## Error Types

- `ClaudeSDKError`: Base exception class
- `CLINotFoundError`: Claude Code CLI not installed
- `CLIConnectionError`: Connection to Claude Code failed
- `ProcessError`: Claude Code process failed
- `CLIJSONDecodeError`: JSON parsing failed
