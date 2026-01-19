# Subagents

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/subagents

Define and invoke subagents for focused subtasks.

## Benefits

- **Context management**: Subagents maintain separate context
- **Parallelization**: Multiple subagents can run concurrently
- **Specialized instructions**: Each can have tailored prompts
- **Tool restrictions**: Limit which tools each can use

## Creating Subagents

```python
from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition

async for message in query(
    prompt="Review the authentication module for security issues",
    options=ClaudeAgentOptions(
        # Task tool required for subagent invocation
        allowed_tools=["Read", "Grep", "Glob", "Task"],
        agents={
            "code-reviewer": AgentDefinition(
                description="Expert code reviewer. Use for quality, security, and maintainability reviews.",
                prompt="""You are a code review specialist with expertise in security.

When reviewing code:
- Identify security vulnerabilities
- Check for performance issues
- Verify adherence to coding standards
- Suggest specific improvements""",
                tools=["Read", "Grep", "Glob"],  # Read-only
                model="sonnet"
            ),
            "test-runner": AgentDefinition(
                description="Runs and analyzes test suites.",
                prompt="You are a test execution specialist.",
                tools=["Bash", "Read", "Grep"]
            )
        }
    )
):
    if hasattr(message, "result"):
        print(message.result)
```

## AgentDefinition

| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `description` | `str` | Yes | When to use this agent |
| `prompt` | `str` | Yes | The agent's system prompt |
| `tools` | `list[str]` | No | Allowed tools (inherits all if omitted) |
| `model` | `str` | No | Model override (`sonnet`, `opus`, `haiku`) |

**Note**: Subagents cannot spawn their own subagents. Don't include `Task` in a subagent's tools.

## Invocation

### Automatic

Claude decides based on the `description` field.

### Explicit

```python
prompt="Use the code-reviewer agent to check the authentication module"
```

## Dynamic Configuration

```python
def create_security_agent(security_level: str) -> AgentDefinition:
    is_strict = security_level == "strict"
    return AgentDefinition(
        description="Security code reviewer",
        prompt=f"You are a {'strict' if is_strict else 'balanced'} security reviewer...",
        tools=["Read", "Grep", "Glob"],
        model="opus" if is_strict else "sonnet"
    )

agents={"security-reviewer": create_security_agent("strict")}
```

## Tool Combinations

| Use case | Tools |
|:---------|:------|
| Read-only analysis | `Read`, `Grep`, `Glob` |
| Test execution | `Bash`, `Read`, `Grep` |
| Code modification | `Read`, `Edit`, `Write`, `Grep`, `Glob` |
| Full access | Omit `tools` field |

## Resuming Subagents

```python
import re

def extract_agent_id(text: str) -> str | None:
    match = re.search(r"agentId:\s*([a-f0-9-]+)", text)
    return match.group(1) if match else None

# First query
agent_id = None
session_id = None

async for message in query(
    prompt="Use the Explore agent to find all API endpoints",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Grep", "Glob", "Task"])
):
    if hasattr(message, "session_id"):
        session_id = message.session_id
    if hasattr(message, "content"):
        extracted = extract_agent_id(str(message.content))
        if extracted:
            agent_id = extracted

# Resume the subagent
if agent_id and session_id:
    async for message in query(
        prompt=f"Resume agent {agent_id} and list the top 3 most complex endpoints",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Grep", "Glob", "Task"],
            resume=session_id
        )
    ):
        if hasattr(message, "result"):
            print(message.result)
```
