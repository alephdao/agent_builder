# MCP Servers

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/mcp

Connect to external tools via Model Context Protocol (MCP).

## Quick Example

```python
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async for message in query(
    prompt="Use the docs MCP server to explain hooks",
    options=ClaudeAgentOptions(
        mcp_servers={
            "claude-code-docs": {
                "type": "http",
                "url": "https://code.claude.com/docs/mcp"
            }
        },
        allowed_tools=["mcp__claude-code-docs__*"]
    )
):
    if isinstance(message, ResultMessage) and message.subtype == "success":
        print(message.result)
```

## Transport Types

### stdio servers

Local processes communicating via stdin/stdout:

```python
mcp_servers={
    "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
            "GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]
        }
    }
}
```

### HTTP/SSE servers

Cloud-hosted MCP servers:

```python
mcp_servers={
    "remote-api": {
        "type": "sse",
        "url": "https://api.example.com/mcp/sse",
        "headers": {
            "Authorization": f"Bearer {os.environ['API_TOKEN']}"
        }
    }
}
```

## Tool Naming

MCP tools follow the pattern: `mcp__<server-name>__<tool-name>`

Example: `mcp__github__list_issues`

## Allowing Tools

```python
allowed_tools=[
    "mcp__github__*",              # All tools from github
    "mcp__db__query",              # Only query from db
    "mcp__slack__send_message"     # Only send_message from slack
]
```

## Config File

Create `.mcp.json` at project root:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## Tool Search

For large tool sets, use MCP tool search:

```python
env={
    "ENABLE_TOOL_SEARCH": "auto"  # or "auto:5" for 5% threshold
}
```

## Example: Database Query

```python
connection_string = os.environ["DATABASE_URL"]

async for message in query(
    prompt="How many users signed up last week?",
    options=ClaudeAgentOptions(
        mcp_servers={
            "postgres": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres", connection_string]
            }
        },
        allowed_tools=["mcp__postgres__query"]
    )
):
    if isinstance(message, ResultMessage) and message.subtype == "success":
        print(message.result)
```
