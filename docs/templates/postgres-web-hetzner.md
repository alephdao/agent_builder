# Template: Postgres + Web Frontend + Hetzner Deployment

Reference implementation: `/Users/philipgalebach/coding-projects/_agents/smithers`

Use this template when the user wants:
- PostgreSQL database (hosted or local)
- Custom web frontend (Next.js)
- Production deployment on Hetzner
- Multi-user support with authentication
- Composio integrations (Calendar, Asana, Slack, etc.)

## Directory Structure

```
{agent-name}/
├── apps/
│   ├── agent/                      # Python backend (Claude Agent SDK)
│   │   ├── main.py                 # Entry point with ClaudeSDKClient
│   │   ├── config.py               # Environment configuration
│   │   ├── db.py                   # Async database operations (asyncpg)
│   │   ├── mcp_tools.py            # MCP tool definitions
│   │   ├── user_context.py         # Dynamic system prompt builder
│   │   ├── integrations/           # Composio integration modules
│   │   │   ├── __init__.py         # ComposioClient singleton
│   │   │   ├── calendar.py         # Google Calendar
│   │   │   ├── asana.py            # Asana tasks
│   │   │   └── slack.py            # Slack messaging
│   │   ├── prompts/
│   │   │   └── system_prompt.md    # Agent system prompt
│   │   ├── .env.example
│   │   └── requirements.txt
│   │
│   └── web/                        # Next.js frontend
│       ├── app/
│       │   ├── api/
│       │   │   ├── chat/route.ts   # SSE streaming endpoint
│       │   │   └── agents/route.ts # Agent CRUD
│       │   ├── (dashboard)/
│       │   │   ├── chat/           # Chat UI
│       │   │   └── settings/       # User settings
│       │   └── middleware.ts       # Clerk authentication
│       ├── components/
│       │   └── chat/               # Chat UI components
│       ├── package.json
│       └── .env.example
│
├── lib/                            # Shared Python modules
│   ├── models.py                   # SQLAlchemy table definitions
│   └── db_ops.py                   # Database operations
│
├── config/
│   └── config.json                 # Multi-company configuration
│
├── alembic/                        # Database migrations
│   ├── alembic.ini
│   └── versions/
│
├── db/
│   └── schema.sql                  # PostgreSQL schema reference
│
├── scripts/
│   ├── setup_postgres_hetzner.sh
│   └── setup_autossh.sh
│
├── .claude/
│   ├── commands/
│   │   └── hetzner-deploy.md
│   └── skills/
│
└── CLAUDE.md
```

## Database Schema (PostgreSQL)

```sql
-- Users authenticated via Clerk
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_id VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE,
    name VARCHAR,
    composio_entity_id VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT,
    tool_calls JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent-specific data (flexible schema)
CREATE TABLE user_agent_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Claude Agent SDK Pattern

```python
# apps/agent/main.py
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock, ToolUseBlock

async def run_agent(user_id: str, conversation_id: str, message: str):
    # Load system prompt with user context
    system_prompt = await build_system_prompt(user_id)

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        system_prompt=system_prompt,
        permission_mode="bypassPermissions",
        model="claude-sonnet-4-5-20250514",
        max_turns=50,
        mcp_servers={"tools": mcp_server},
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query(message)

        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        yield block.text
                    elif isinstance(block, ToolUseBlock):
                        logger.info(f"Tool call: {block.name}")
```

## MCP Tools Pattern

```python
# apps/agent/mcp_tools.py
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool
def query_database(sql: str) -> str:
    """
    Execute a read-only SQL query against the database.
    Only SELECT queries are allowed.
    """
    # Validate query is SELECT only
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries allowed"

    # Execute with user scoping
    result = await db.fetch(sql, user_id=get_current_user_id())
    return json.dumps(result)

@tool
def calendar_list_events(days: int = 7) -> str:
    """List upcoming calendar events."""
    from integrations.calendar import list_events
    events = list_events(days=days, entity_id=get_entity_id())
    return json.dumps(events)

# Create MCP server
mcp_server = create_sdk_mcp_server(
    name="agent-tools",
    version="1.0.0",
    tools=[query_database, calendar_list_events, ...]
)
```

## Composio Integration Pattern

```python
# apps/agent/integrations/__init__.py
from composio import ComposioToolSet

class ComposioClient:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = ComposioToolSet()
        return cls._instance

# apps/agent/integrations/calendar.py
def list_events(days: int = 7, entity_id: str = None) -> list[dict]:
    client = ComposioClient.get()
    result = client.execute(
        action="GOOGLECALENDAR_EVENTS_LIST",
        params={"days": days},
        entity_id=entity_id,
    )
    return result.get("data", {}).get("events", [])
```

## Environment Variables

```bash
# apps/agent/.env

# Claude Agent SDK (OAuth from ~/.claude/ or API key)
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/agentdb

# Composio (for integrations)
COMPOSIO_API_KEY=...
COMPOSIO_DEFAULT_ENTITY=default

# Environment
AGENT_ENV=development
```

```bash
# apps/web/.env

# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...

# Database (same as agent)
DATABASE_URL=postgresql://user:pass@localhost:5432/agentdb

# Agent API
AGENT_API_URL=http://localhost:8000
```

## Hetzner Deployment

### Server Setup

```bash
# Hetzner VPS via Tailscale VPN
# SSH: admin@100.109.131.85

# Services:
# - PostgreSQL (port 5432)
# - Next.js web app (port 3000)
# - systemd service: {agent-name}.service
```

### Deploy Script Pattern

```bash
# Commit and push
git add -A && git commit -m "Deploy: <description>" && git push

# SSH to server and pull
ssh admin@100.109.131.85 "cd /opt/{agent-name} && git pull"

# Install dependencies
ssh admin@100.109.131.85 "cd /opt/{agent-name}/apps/web && npm install && npm run build"

# Restart service
ssh admin@100.109.131.85 "sudo systemctl restart {agent-name}"
```

### SSH Tunnel for Local Development

```bash
# Tunnel to access remote Postgres locally
ssh -L 15432:localhost:5432 deploy@100.109.131.85

# Local DATABASE_URL uses port 15432
# Server DATABASE_URL uses port 5432
```

## Web API Pattern (Next.js)

```typescript
// apps/web/app/api/chat/route.ts
import { spawn } from 'child_process';

export async function POST(request: NextRequest) {
  const { userId } = getAuth(request);
  const { conversationId, message } = await request.json();

  // Spawn Python agent as subprocess
  const process = spawn('python3', [
    '-m', 'apps.agent.main',
    '--user-id', userId,
    '--conversation-id', conversationId,
    '--message', message,
  ]);

  // Stream responses as Server-Sent Events
  return new Response(
    new ReadableStream({
      async start(controller) {
        process.stdout.on('data', (chunk) => {
          controller.enqueue(`data: ${JSON.stringify({text: chunk.toString()})}\n\n`);
        });
        process.on('close', () => controller.close());
      }
    }),
    { headers: { 'Content-Type': 'text/event-stream' } }
  );
}
```

## System Prompt Pattern

```markdown
# {Agent Name}

You are {name}, a {description}.

## Your Purpose

{detailed purpose and goals}

## Personality & Tone

- {tone guideline 1}
- {tone guideline 2}
- {tone guideline 3}

## Available Tools

### Database Access
- `query_database(sql)` - Execute read-only SQL queries

### Calendar (Google Calendar via Composio)
- `calendar_list_events(days)` - List upcoming events
- `calendar_create_event(title, start, end)` - Create new event

### {Other Integration}
- `{tool_name}({params})` - {description}

## User Context

{Dynamically injected at runtime:}
- Connected integrations
- User preferences
- Recent activity

## Guidelines

1. {guideline 1}
2. {guideline 2}
3. {guideline 3}

## What You Should NEVER Do

- {restriction 1}
- {restriction 2}
- {restriction 3}
```

## Key Patterns Summary

| Pattern | Implementation |
|---------|---------------|
| **Database** | asyncpg with connection pooling |
| **Auth** | Clerk (web) → internal UUID |
| **Multi-tenant** | user_id scoping on all queries |
| **Integrations** | Composio with entity_id per user |
| **Streaming** | SSE from Next.js API route |
| **Deployment** | Git pull + systemd restart |
| **Migrations** | Alembic for schema changes |
