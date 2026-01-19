# Agent Builder

A Claude Code slash command that builds complete AI agents. Run `/build-agent` to start.

## Directory Structure

Everything is in `docs/`:

```
agent_prompt_builder/
├── .claude/commands/
│   └── build-agent.md          # The main slash command
├── docs/
│   ├── reference-prompts/      # Example system prompts - READ ALL
│   ├── agent-sdk/              # Claude Agent SDK documentation
│   └── templates/              # Architecture templates
├── specs/                      # Generated spec documents (output)
└── CLAUDE.md                   # This file
```

## Reference Prompts

**Location:** `docs/reference-prompts/`

**READ ALL OF THESE** before building an agent. They show what good system prompts look like.

| File | Purpose |
|------|---------|
| `claude-code-system-prompt.md` | **Gold standard** - Read first. Multi-tool orchestration, safety rules, tone guidelines |
| `claude-code-tools.md` | How to document tools in prompts |
| `aristotle-companion.md` | Conversational personality, Socratic dialogue, tone constraints |
| `perplexity.md` | Search/research agent patterns |


## Claude Agent SDK Documentation

**Location:** `docs/agent-sdk/`

| File | Purpose |
|------|---------|
| `00-overview.md` | SDK overview and concepts |
| `01-quickstart.md` | Getting started guide |
| `02-python-reference.md` | **Python API 

reference** - ClaudeSDKClient, ClaudeAgentOptions, tool decorator |
| `03-hooks.md` | Event hooks |
| `04-mcp-servers.md` | MCP tool servers |
| `05-permissions.md` | Permission modes |
| `06-sessions.md` | Session management |
| `07-subagents.md` | Subagent patterns |
| `08-custom-tools.md` | Custom tool patterns |

## Architecture Templates

**Location:** `docs/templates/`

### 1. Full-Stack: Postgres + Web + Hetzner

**File:** `docs/templates/postgres-web-hetzner.md`

**Reference Implementation:** `/Users/philipgalebach/coding-projects/_agents/smithers`

Use when you need:
- PostgreSQL database (asyncpg)
- Next.js web frontend with Clerk auth
- Hetzner deployment via Tailscale
- Composio integrations (Calendar, Asana, Slack)
- Multi-user support

### 2. Lightweight: SQLite + Telegram

**File:** `docs/templates/sqlite-telegram.md`

**Reference Implementation:** `/Users/philipgalebach/coding-projects/_agents/spanish-translator/telegram_bot`

Use when you need:
- SQLite or JSON file storage
- Telegram bot interface (aiogram)
- Single-purpose agent
- Simple deployment

### 3. Supabase MCP Integration

**File:** `docs/templates/supabase-mcp.md`

Use when you need:
- Managed PostgreSQL via Supabase (no database management overhead)
- MCP connection for direct database operations
- Read/write database access without custom tools
- Rapid prototyping with hosted infrastructure

**MCP Server:** `https://mcp.supabase.com/mcp`

Setup:
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

Authenticate via: `claude /mcp` → select "supabase" → "Authenticate"

## Reference Implementations

These are working agents you can explore to understand patterns:

### Smithers (Full-Stack)
```
/Users/philipgalebach/coding-projects/_agents/smithers
```
- Postgres + Next.js + Hetzner + Composio
- Multi-agent support
- OAuth via Composio for Calendar, Asana, Slack
- Clerk authentication
- SSE streaming responses

### Spanish Translator (Telegram Bot)
```
/Users/philipgalebach/coding-projects/_agents/spanish-translator/telegram_bot
```
- JSON file storage
- Telegram bot via aiogram
- Per-user Claude clients
- Voice transcription support

## How /build-agent Works

1. **Architecture Selection** - Asks 4 questions to determine template:
   - Interface (Telegram / Web / CLI)
   - Database (SQLite / Postgres / Supabase MCP)
   - Integrations (None / Composio / Custom)
   - Deployment (Local / Hetzner)

2. **Deep Interview** - 8 rounds of non-obvious questions about:
   - Core identity & purpose
   - Personality & tone
   - Technical implementation
   - Data & state
   - Tools & capabilities
   - Edge cases & safety
   - User experience
   - Examples

3. **Spec Generation** - Creates `specs/agent-spec-{slug}.md`

4. **Build** - After approval, creates project at:
   ```
   /Users/philipgalebach/coding-projects/_agents/{slug}/
   ```
