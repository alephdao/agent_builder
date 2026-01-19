# Agent SDK Overview

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/overview

Build production AI agents with Claude Code as a library.

## Installation

```bash
pip install claude-agent-sdk
```

## Quick Example

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="Find and fix the bug in auth.py",
        options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"])
    ):
        print(message)

asyncio.run(main())
```

## Built-in Tools

| Tool | What it does |
|------|--------------|
| **Read** | Read any file in the working directory |
| **Write** | Create new files |
| **Edit** | Make precise edits to existing files |
| **Bash** | Run terminal commands, scripts, git operations |
| **Glob** | Find files by pattern |
| **Grep** | Search file contents with regex |
| **WebSearch** | Search the web for current information |
| **WebFetch** | Fetch and parse web page content |
| **AskUserQuestion** | Ask the user clarifying questions |

## Key Features

- **Built-in tools**: Read, write, edit files and run commands out of the box
- **Hooks**: Run custom code at key points in the agent lifecycle
- **Subagents**: Spawn specialized agents to handle focused subtasks
- **MCP**: Connect to external systems via Model Context Protocol
- **Permissions**: Control exactly which tools your agent can use
- **Sessions**: Maintain context across multiple exchanges

## Authentication

```bash
export ANTHROPIC_API_KEY=your-api-key
```

Also supports:
- **Amazon Bedrock**: set CLAUDE_CODE_USE_BEDROCK=1
- **Google Vertex AI**: set CLAUDE_CODE_USE_VERTEX=1
- **Microsoft Foundry**: set CLAUDE_CODE_USE_FOUNDRY=1

## SDK vs Client SDK

The Anthropic Client SDK gives you direct API access where you implement tool execution yourself. The Agent SDK gives you Claude with built-in tool execution:

```python
# Agent SDK: Claude handles tools autonomously
async for message in query(prompt="Fix the bug in auth.py"):
    print(message)
```
