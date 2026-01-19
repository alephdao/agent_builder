# Permissions

> Pulled: 2026-01-17 11:01:55 -03
> Source: https://platform.claude.com/docs/en/agent-sdk/permissions

Control how your agent uses tools.

## Permission Evaluation Order

1. **Hooks**: Run first, can allow/deny/continue
2. **Permission rules**: Check deny → allow → ask rules
3. **Permission mode**: Apply the active mode
4. **canUseTool callback**: If not resolved, call your callback

## Permission Modes

| Mode | Description | Tool behavior |
|:-----|:------------|:--------------|
| `default` | Standard behavior | Unmatched tools trigger `canUseTool` callback |
| `acceptEdits` | Auto-accept file edits | File operations auto-approved |
| `dontAsk` | Skip approval prompts | Auto-deny unless explicitly allowed |
| `bypassPermissions` | Bypass all checks | All tools run without prompts |

**Warning**: `bypassPermissions` is inherited by all subagents and cannot be overridden.

## Setting Permission Mode

### At query time

```python
async for message in query(
    prompt="Help me refactor this code",
    options=ClaudeAgentOptions(
        permission_mode="acceptEdits"
    )
):
    print(message)
```

### During streaming

```python
q = query(
    prompt="Help me refactor this code",
    options=ClaudeAgentOptions(permission_mode="default")
)

# Change mode mid-session
await q.set_permission_mode("acceptEdits")

async for message in q:
    print(message)
```

## Accept Edits Mode

Auto-approves:
- File edits (Edit, Write tools)
- Filesystem commands: `mkdir`, `touch`, `rm`, `mv`, `cp`

Other tools still require normal permissions.

## Don't Ask Mode

Auto-denies all tools unless explicitly permitted by an allow rule. No prompts shown.

Use for non-interactive environments (CI/CD).

## Custom Permission Handler

```python
from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny

async def custom_permission_handler(
    tool_name: str,
    input_data: dict,
    context: dict
) -> PermissionResultAllow | PermissionResultDeny:

    # Block writes to system directories
    if tool_name == "Write" and input_data.get("file_path", "").startswith("/system/"):
        return PermissionResultDeny(
            message="System directory write not allowed",
            interrupt=True
        )

    # Redirect config operations
    if tool_name in ["Write", "Edit"] and "config" in input_data.get("file_path", ""):
        safe_path = f"./sandbox/{input_data['file_path']}"
        return PermissionResultAllow(
            updated_input={**input_data, "file_path": safe_path}
        )

    return PermissionResultAllow(updated_input=input_data)

options = ClaudeAgentOptions(
    can_use_tool=custom_permission_handler,
    allowed_tools=["Read", "Write", "Edit"]
)
```
