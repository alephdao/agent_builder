# Quickstart

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/quickstart

Build an AI agent that reads your code, finds bugs, and fixes them.

## Prerequisites

- Python 3.10+
- An Anthropic account

## Setup

### 1. Install Claude Code

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### 2. Create a project folder

```bash
mkdir my-agent && cd my-agent
```

### 3. Install the SDK

```bash
# Using uv (recommended)
uv init && uv add claude-agent-sdk

# Using pip
python3 -m venv .venv && source .venv/bin/activate
pip3 install claude-agent-sdk
```

### 4. Set your API key

Create a `.env` file:
```bash
ANTHROPIC_API_KEY=your-api-key
```

## Create a buggy file

Create `utils.py` with intentional bugs:

```python
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)  # Bug: division by zero if empty

def get_user_name(user):
    return user["name"].upper()  # Bug: crashes if user is None
```

## Build the agent

Create `agent.py`:

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():
    async for message in query(
        prompt="Review utils.py for bugs that would cause crashes. Fix any issues you find.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob"],
            permission_mode="acceptEdits"
        )
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")

asyncio.run(main())
```

## Run your agent

```bash
python3 agent.py
```

## Key Concepts

### Tools

| Tools | What the agent can do |
|-------|----------------------|
| `Read`, `Glob`, `Grep` | Read-only analysis |
| `Read`, `Edit`, `Glob` | Analyze and modify code |
| `Read`, `Edit`, `Bash`, `Glob`, `Grep` | Full automation |

### Permission Modes

| Mode | Behavior | Use case |
|------|----------|----------|
| `acceptEdits` | Auto-approves file edits | Trusted development workflows |
| `bypassPermissions` | Runs without prompts | CI/CD pipelines |
| `default` | Requires `canUseTool` callback | Custom approval flows |
