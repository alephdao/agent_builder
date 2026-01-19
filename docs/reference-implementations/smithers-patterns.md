# Smithers: Full-Stack Agent Pattern

Reference implementation for Postgres + Next.js + Hetzner + Composio architecture.

## Directory Structure

```
smithers/
├── apps/
│   ├── agent/                    # Backend: Claude Agent SDK
│   │   ├── main.py              # Agent entry point
│   │   ├── config.py            # Configuration management
│   │   ├── db.py                # Database operations class
│   │   ├── mcp_tools.py         # MCP tool integrations
│   │   ├── user_context.py      # User context builder
│   │   ├── permissions.py       # Permission management
│   │   ├── tools/               # Custom tool implementations
│   │   │   ├── __init__.py
│   │   │   ├── asana_tools.py
│   │   │   ├── calendar_tools.py
│   │   │   └── slack_tools.py
│   │   ├── integrations/        # Composio integration wrappers
│   │   │   ├── __init__.py
│   │   │   ├── asana.py
│   │   │   ├── google_calendar.py
│   │   │   └── slack.py
│   │   ├── prompts/             # System prompts
│   │   │   └── smithers_system_prompt.md
│   │   ├── requirements.txt
│   │   └── .env.example
│   └── web/                     # Frontend: Next.js
│       ├── app/
│       │   ├── api/             # API routes
│       │   │   ├── agent/       # Agent communication endpoints
│       │   │   │   └── route.ts  # POST /api/agent (streaming)
│       │   │   └── auth/        # Clerk webhooks
│       │   ├── layout.tsx
│       │   └── page.tsx
│       ├── components/
│       │   ├── Agent.tsx        # Agent chat interface
│       │   └── ui/              # shadcn/ui components
│       ├── lib/
│       │   ├── db.ts            # Database client (Postgres)
│       │   └── utils.ts
│       ├── package.json
│       └── .env.local.example
├── alembic/                     # Database migrations
│   ├── versions/
│   └── env.py
├── alembic.ini
├── lib/                         # Shared libraries
│   ├── __init__.py
│   ├── database.py              # Async Postgres connection
│   ├── models.py                # SQLAlchemy models
│   └── db_ops.py                # Database helper functions
├── config/
│   └── database.json            # Database configuration
├── .gitignore
└── README.md
```

## Core Components

### 1. Agent Entry Point (`apps/agent/main.py`)

```python
#!/usr/bin/env python3
"""
Smithers Agent Entry Point
Handles user input, loads configuration, creates agent with Claude SDK
"""

import asyncio
import sys
from pathlib import Path
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    query,
)

from .config import get_config
from .db import get_db, AgentDB
from .mcp_tools import create_filtered_mcp_server
from .user_context import UserContextBuilder


def load_system_prompt(user_email: str = None) -> str:
    """Load system prompt from prompts/ directory"""
    prompts_dir = Path(__file__).parent / "prompts"
    prompt_path = prompts_dir / "smithers_system_prompt.md"

    if prompt_path.exists():
        return prompt_path.read_text()

    return "You are Smithers, an AI assistant."


async def run_agent(
    user_id: str,
    conversation_id: str,
    message: str,
    db: AgentDB
):
    """Run the agent with the given message"""

    # Load user context
    user = await db.get_user_by_id(user_id)
    context_builder = UserContextBuilder(db, user_id)
    user_context = await context_builder.build_context()

    # Create system prompt with context
    base_prompt = load_system_prompt(user.get('email'))
    system_prompt = f"{base_prompt}\n\n{user_context}"

    # Load conversation history
    history = await db.get_conversation_messages(conversation_id)

    # Configure agent options
    config = get_config()
    options = ClaudeAgentOptions(
        cwd=config.agent_cwd,
        system_prompt=system_prompt,
        model="claude-sonnet-4-5-20241022",
        permission_mode="allowAll",  # or "requestPermission"
        max_turns=20,
    )

    # Create MCP tool server (optional)
    mcp_server = create_filtered_mcp_server(user_id, db)
    if mcp_server:
        options.custom_mcp_servers = [mcp_server]

    # Run agent with streaming
    async with ClaudeSDKClient(options=options) as client:
        async for chunk in client.stream(message, history=history):
            # Stream to stdout as SSE or handle chunks
            if chunk.type == "text":
                print(chunk.content, end="", flush=True)
            elif chunk.type == "tool_use":
                # Log tool usage
                pass

        # Save conversation to database
        await db.save_message(conversation_id, "user", message)
        await db.save_message(conversation_id, "assistant", client.last_response)


async def main():
    """Entry point"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--message", help="Message (or read from stdin)")
    args = parser.parse_args()

    message = args.message or sys.stdin.read()

    db = await get_db()
    try:
        await run_agent(args.user_id, args.conversation_id, message, db)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Database Operations (`apps/agent/db.py`)

```python
"""Database operations for agent"""

import asyncpg
from typing import Optional, List, Dict
from datetime import datetime


class AgentDB:
    """Agent database operations wrapper"""

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by internal ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            return dict(row) if row else None

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get conversation history"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
                LIMIT $2
                """,
                conversation_id,
                limit
            )
            return [dict(row) for row in rows]

    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str
    ):
        """Save a message to the database"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages (conversation_id, role, content)
                VALUES ($1, $2, $3)
                """,
                conversation_id,
                role,
                content
            )

    async def close(self):
        """Close database pool"""
        await self.pool.close()


async def get_db() -> AgentDB:
    """Create database connection pool"""
    import os

    database_url = os.getenv("DATABASE_URL")
    pool = await asyncpg.create_pool(database_url)
    return AgentDB(pool)
```

### 3. User Context Builder (`apps/agent/user_context.py`)

```python
"""Build user context for system prompt injection"""

from typing import Dict
from .db import AgentDB


class UserContextBuilder:
    """Builds user context for Claude"""

    def __init__(self, db: AgentDB, user_id: str):
        self.db = db
        self.user_id = user_id

    async def build_context(self) -> str:
        """Build complete user context"""

        # Get user preferences
        user = await self.db.get_user_by_id(self.user_id)

        # Get recent tasks
        tasks = await self.db.get_user_tasks(self.user_id, limit=10)

        # Get upcoming meetings
        meetings = await self.db.get_upcoming_meetings(self.user_id, limit=5)

        # Format context
        context_parts = [
            "# User Context",
            f"",
            f"User: {user['name']} ({user['email']})",
            f"",
            f"## Recent Tasks ({len(tasks)} total)",
        ]

        for task in tasks:
            context_parts.append(f"- [{task['status']}] {task['title']}")

        context_parts.extend([
            f"",
            f"## Upcoming Meetings ({len(meetings)} total)",
        ])

        for meeting in meetings:
            context_parts.append(
                f"- {meeting['title']} at {meeting['start_time']}"
            )

        return "\n".join(context_parts)
```

### 4. Custom Tools (`apps/agent/tools/asana_tools.py`)

```python
"""Asana integration tools using Composio"""

from claude_agent_sdk import tool
from ..integrations.asana import AsanaClient


@tool
async def create_asana_task(
    title: str,
    description: str = "",
    assignee_email: str = None,
    due_date: str = None,
) -> dict:
    """
    Create a task in Asana.

    Args:
        title: Task title
        description: Task description
        assignee_email: Email of person to assign to
        due_date: Due date in YYYY-MM-DD format

    Returns:
        Created task details
    """
    client = AsanaClient()
    task = await client.create_task(
        title=title,
        description=description,
        assignee_email=assignee_email,
        due_date=due_date,
    )
    return {
        "task_id": task["gid"],
        "title": task["name"],
        "permalink_url": task["permalink_url"],
    }


@tool
async def list_asana_tasks(workspace_id: str = None, limit: int = 20) -> list:
    """
    List Asana tasks.

    Args:
        workspace_id: Optional workspace ID to filter
        limit: Maximum number of tasks to return

    Returns:
        List of tasks
    """
    client = AsanaClient()
    tasks = await client.list_tasks(workspace_id=workspace_id, limit=limit)
    return [
        {
            "task_id": task["gid"],
            "title": task["name"],
            "status": task["completed"],
        }
        for task in tasks
    ]
```

### 5. Next.js API Route (`apps/web/app/api/agent/route.ts`)

```typescript
import { auth } from "@clerk/nextjs";
import { spawn } from "child_process";

export async function POST(req: Request) {
  const { userId } = auth();
  if (!userId) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { message, conversationId } = await req.json();

  // Create SSE stream
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      // Spawn Python agent process
      const agentProcess = spawn("python", [
        "-m",
        "apps.agent.main",
        "--user-id",
        userId,
        "--conversation-id",
        conversationId,
        "--message",
        message,
      ]);

      // Stream stdout
      agentProcess.stdout.on("data", (data) => {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ text: data.toString() })}\n\n`)
        );
      });

      // Handle completion
      agentProcess.on("close", (code) => {
        controller.enqueue(encoder.encode(`data: [DONE]\n\n`));
        controller.close();
      });

      // Handle errors
      agentProcess.stderr.on("data", (data) => {
        console.error("Agent error:", data.toString());
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
```

### 6. Configuration (`apps/agent/.env.example`)

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/smithers

# Composio (optional)
COMPOSIO_API_KEY=...

# Clerk (for web auth)
CLERK_SECRET_KEY=...

# Agent settings
AGENT_CWD=/path/to/working/directory
AGENT_PERMISSION_MODE=allowAll
AGENT_MAX_TURNS=20
```

### 7. Database Schema (Alembic Migration)

```python
"""Initial schema

Revision ID: 001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


def upgrade():
    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('clerk_id', sa.String(), unique=True),
        sa.Column('email', sa.String(), unique=True),
        sa.Column('name', sa.String()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Conversations table
    op.create_table(
        'conversations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('title', sa.String()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Messages table
    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id')),
        sa.Column('role', sa.String()),  # 'user' or 'assistant'
        sa.Column('content', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('users')
```

## Key Patterns

### Composio Integration

Composio provides OAuth for Calendar, Asana, Slack via their API:

```python
# apps/agent/integrations/asana.py
import os
from composio import Composio

class AsanaClient:
    def __init__(self):
        self.client = Composio(api_key=os.getenv("COMPOSIO_API_KEY"))

    async def create_task(self, title: str, **kwargs):
        """Create task via Composio"""
        return await self.client.execute_action(
            action="ASANA_CREATE_TASK",
            params={
                "name": title,
                **kwargs
            }
        )
```

### Permission Management

```python
# apps/agent/permissions.py
from claude_agent_sdk import PermissionCallback

class SmithersPermissions(PermissionCallback):
    async def request_permission(self, tool_name: str, args: dict) -> bool:
        # Auto-approve read-only operations
        read_only = ["list_", "get_", "search_"]
        if any(tool_name.startswith(prefix) for prefix in read_only):
            return True

        # Require approval for writes
        return False  # Will prompt user
```

### Deployment (Hetzner via Tailscale)

```bash
# Deploy to Hetzner server
ssh root@<hetzner-ip>

# Setup
cd /opt/smithers
python -m venv .venv
source .venv/bin/activate
pip install -r apps/agent/requirements.txt

# Run database migrations
alembic upgrade head

# Run agent (systemd service)
systemctl start smithers-agent

# Next.js web app
cd apps/web
npm install
npm run build
npm start
```

## Summary

This pattern is ideal for:
- Multi-user web applications
- Production deployments
- Complex integrations (Calendar, Asana, Slack)
- Scalable database requirements
- OAuth-based authentication
