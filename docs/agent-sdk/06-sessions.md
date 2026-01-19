# Sessions

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/sessions

Manage conversation state and resumption.

## Getting the Session ID

```python
from claude_agent_sdk import query, ClaudeAgentOptions

session_id = None

async for message in query(
    prompt="Help me build a web application",
    options=ClaudeAgentOptions(model="claude-sonnet-4-5")
):
    if hasattr(message, 'subtype') and message.subtype == 'init':
        session_id = message.data.get('session_id')
        print(f"Session started with ID: {session_id}")

    print(message)
```

## Resuming Sessions

```python
# Resume a previous session
async for message in query(
    prompt="Continue implementing the authentication system",
    options=ClaudeAgentOptions(
        resume="session-xyz",  # Session ID from previous conversation
        allowed_tools=["Read", "Edit", "Write", "Glob", "Grep", "Bash"]
    )
):
    print(message)
```

## Forking Sessions

Create a new branch from an existing session without modifying the original.

### When to Fork

- Explore different approaches from the same starting point
- Create multiple conversation branches
- Test changes without affecting original history

### Comparison

| Behavior | `fork_session=False` | `fork_session=True` |
|----------|---------------------|---------------------|
| Session ID | Same as original | New ID generated |
| History | Appends to original | Creates new branch |
| Original Session | Modified | Preserved unchanged |

### Example

```python
# First query
session_id = None
async for message in query(
    prompt="Help me design a REST API",
    options=ClaudeAgentOptions(model="claude-sonnet-4-5")
):
    if hasattr(message, 'subtype') and message.subtype == 'init':
        session_id = message.data.get('session_id')

# Fork to try a different approach
async for message in query(
    prompt="Now let's redesign this as a GraphQL API instead",
    options=ClaudeAgentOptions(
        resume=session_id,
        fork_session=True  # Creates a new session ID
    )
):
    if hasattr(message, 'subtype') and message.subtype == 'init':
        forked_id = message.data.get('session_id')
        print(f"Forked session: {forked_id}")

# Original session unchanged - can still resume it
async for message in query(
    prompt="Add authentication to the REST API",
    options=ClaudeAgentOptions(
        resume=session_id,
        fork_session=False  # Continue original (default)
    )
):
    print(message)
```
