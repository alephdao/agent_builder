# Hooks

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/hooks

Intercept and customize agent behavior at key execution points.

## Overview

Hooks let you:
- **Block dangerous operations** before they execute
- **Log and audit** every tool call
- **Transform inputs and outputs**
- **Require human approval** for sensitive actions
- **Track session lifecycle**

## Available Hooks

| Hook Event | Description |
|------------|-------------|
| `PreToolUse` | Before tool execution (can block or modify) |
| `PostToolUse` | After tool execution result |
| `UserPromptSubmit` | When user submits a prompt |
| `Stop` | When agent execution stops |
| `SubagentStop` | When a subagent completes |
| `PreCompact` | Before conversation compaction |

## Basic Example

```python
from claude_agent_sdk import query, ClaudeAgentOptions, HookMatcher

async def protect_env_files(input_data, tool_use_id, context):
    file_path = input_data['tool_input'].get('file_path', '')

    if file_path.endswith('.env'):
        return {
            'hookSpecificOutput': {
                'hookEventName': input_data['hook_event_name'],
                'permissionDecision': 'deny',
                'permissionDecisionReason': 'Cannot modify .env files'
            }
        }
    return {}

async for message in query(
    prompt="Update the database configuration",
    options=ClaudeAgentOptions(
        hooks={
            'PreToolUse': [HookMatcher(matcher='Write|Edit', hooks=[protect_env_files])]
        }
    )
):
    print(message)
```

## Hook Matchers

```python
@dataclass
class HookMatcher:
    matcher: str | None = None        # Tool name pattern (regex)
    hooks: list[HookCallback] = field(default_factory=list)
    timeout: float | None = None      # Timeout in seconds (default: 60)
```

## Callback Inputs

Common fields in `input_data`:
- `hook_event_name`: The hook type
- `session_id`: Current session identifier
- `tool_name`: Name of the tool being called
- `tool_input`: Arguments passed to the tool
- `tool_response`: Result from tool execution (PostToolUse)

## Callback Outputs

```python
return {
    'continue': True,  # Whether agent should continue
    'systemMessage': 'Context for Claude',
    'hookSpecificOutput': {
        'hookEventName': input_data['hook_event_name'],
        'permissionDecision': 'allow' | 'deny' | 'ask',
        'permissionDecisionReason': 'Explanation',
        'updatedInput': {...}  # Modified tool input
    }
}
```

## Common Patterns

### Block Dangerous Commands

```python
async def block_dangerous_commands(input_data, tool_use_id, context):
    command = input_data['tool_input'].get('command', '')

    if 'rm -rf /' in command:
        return {
            'hookSpecificOutput': {
                'hookEventName': input_data['hook_event_name'],
                'permissionDecision': 'deny',
                'permissionDecisionReason': 'Dangerous command blocked'
            }
        }
    return {}
```

### Redirect to Sandbox

```python
async def redirect_to_sandbox(input_data, tool_use_id, context):
    if input_data['tool_name'] == 'Write':
        original_path = input_data['tool_input'].get('file_path', '')
        return {
            'hookSpecificOutput': {
                'hookEventName': input_data['hook_event_name'],
                'permissionDecision': 'allow',
                'updatedInput': {
                    **input_data['tool_input'],
                    'file_path': f'/sandbox{original_path}'
                }
            }
        }
    return {}
```

### Audit Logging

```python
async def log_tool_use(input_data, tool_use_id, context):
    print(f"Tool used: {input_data.get('tool_name')}")
    return {}
```
