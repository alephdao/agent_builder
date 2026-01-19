# Template: Supabase MCP Integration

Use this template when the user wants:
- Managed PostgreSQL via Supabase
- MCP connection for database operations
- Read/write database access from Claude Agent SDK
- No custom database management overhead

## Supabase MCP Server

**Server URL:** `https://mcp.supabase.com/mcp`

Supabase provides a hosted MCP server that gives Claude direct access to your Supabase database. This eliminates the need to write custom database tools.

## Setup (Claude Code / CLI)

### 1. Add MCP Server Configuration

Add to your project's `.mcp.json`:

```json
{
  "mcpServers": {
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```

Or via CLI:

```bash
claude mcp add --scope project --transport http supabase "https://mcp.supabase.com/mcp"
```

### 2. Authenticate

In a terminal (not IDE extension), run:

```bash
claude /mcp
```

Select "supabase" server, then "Authenticate" to begin the OAuth flow. This grants Claude access to your Supabase projects.

## Options

| Option | Default | Description |
|--------|---------|-------------|
| Read-only | Off | When enabled, restricts to SELECT queries only |
| Feature Groups | All features except Storage | Enable/disable specific capabilities |

For production agents that only need read access, enable Read-only mode for safety.

## Claude Agent SDK Integration

```python
# apps/agent/main.py
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def run_agent(message: str):
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        permission_mode="bypassPermissions",
        model="claude-sonnet-4-5-20250514",
        max_turns=50,
        mcp_servers={
            "supabase": {
                "type": "http",
                "url": "https://mcp.supabase.com/mcp"
            }
        },
        allowed_tools=["mcp__supabase__*"]
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(message)

        async for msg in client.receive_response():
            # Process messages...
            pass
```

## Available Tools

The Supabase MCP server provides these tools (prefixed with `mcp__supabase__`):

### Database Operations
- `list_tables` - List all tables in the database
- `query` - Execute SQL queries (SELECT, INSERT, UPDATE, DELETE)
- `describe_table` - Get table schema information

### Project Management
- `list_projects` - List your Supabase projects
- `get_project` - Get project details

### Auth (if enabled)
- `list_users` - List auth users
- `create_user` - Create new auth user

## Scoping to a Project

To restrict MCP access to a specific project, select the project in the Supabase MCP dashboard before generating the configuration. When no project is selected, the MCP server has access to all your projects.

## System Prompt Pattern

When using Supabase MCP, include database context in your system prompt:

```markdown
## Database Access

You have direct access to the Supabase database via MCP tools.

### Available Tables
- `users` - User accounts (id, email, name, created_at)
- `conversations` - Chat conversations
- `messages` - Individual messages

### Guidelines
1. Always use parameterized queries to prevent SQL injection
2. Scope queries with user_id when accessing user-specific data
3. Use transactions for multi-step operations
4. Prefer `list_tables` and `describe_table` to understand schema before querying

### Example Queries
```sql
-- Get user's recent conversations
SELECT * FROM conversations
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT 10;

-- Insert new message
INSERT INTO messages (conversation_id, role, content)
VALUES ($1, $2, $3)
RETURNING *;
```
```

## Directory Structure (with Supabase)

```
{agent-name}/
├── apps/
│   └── agent/
│       ├── main.py                 # Claude Agent SDK with Supabase MCP
│       ├── config.py               # Environment configuration
│       ├── user_context.py         # Dynamic system prompt
│       ├── prompts/
│       │   └── system_prompt.md
│       ├── .env.example
│       └── requirements.txt
│
├── supabase/
│   ├── migrations/                 # Supabase migrations
│   └── seed.sql                    # Initial data
│
├── .mcp.json                       # MCP server config (Supabase)
├── .claude/commands/
└── CLAUDE.md
```

## Environment Variables

```bash
# apps/agent/.env

# Claude Agent SDK
ANTHROPIC_API_KEY=sk-ant-...

# Supabase (for direct SDK access if needed)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # Only for admin operations

# Environment
AGENT_ENV=development
```

## When to Use Supabase MCP vs Custom Tools

| Use Supabase MCP | Use Custom Tools |
|------------------|------------------|
| General CRUD operations | Complex business logic |
| Ad-hoc queries | Pre-validated operations |
| Database exploration | Type-safe interfaces |
| Rapid prototyping | Production security |

## Security Considerations

1. **Read-only mode** - Enable for agents that only need to query data
2. **Row Level Security (RLS)** - Enable RLS policies in Supabase for user data isolation
3. **Project scoping** - Restrict MCP to specific project in dashboard
4. **Allowed tools** - Use `allowed_tools` to restrict which MCP tools the agent can use:

```python
allowed_tools=[
    "mcp__supabase__query",      # Only allow queries
    "mcp__supabase__list_tables" # And listing tables
]
```

## Migrations with Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize (creates supabase/ directory)
supabase init

# Create migration
supabase migration new create_users_table

# Apply migrations locally
supabase db push

# Apply to production
supabase db push --linked
```

## Key Patterns Summary

| Pattern | Implementation |
|---------|---------------|
| **Database** | Supabase MCP (hosted PostgreSQL) |
| **Auth** | Supabase Auth or Clerk |
| **Multi-tenant** | RLS policies with user_id |
| **Migrations** | Supabase CLI migrations |
| **MCP Transport** | HTTP to mcp.supabase.com |
