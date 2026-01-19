# Agent Builder

A Claude Code slash command that builds complete AI agents from scratch through an interactive interview process.

## What This Does

Run `/build-agent` in Claude Code and answer questions. The system will:
1. Ask you about your agent's architecture needs
2. Interview you deeply about requirements
3. Generate a detailed specification document
4. Build the complete agent project for you

## Prerequisites

- [Claude Code CLI](https://docs.claude.ai/claude-code) installed
- Basic understanding of what kind of agent you want to build

## Quick Start

1. **Clone this repo:**
   ```bash
   git clone https://github.com/alephdao/agent_builder.git
   cd agent_builder
   ```

2. **Open Claude Code in this directory:**
   ```bash
   claude
   ```

3. **Run the build command:**
   ```
   /build-agent
   ```

4. **Answer the questions:**
   - Architecture questions (8 questions in 2 rounds):
     - Core: interface, storage, data types, integrations
     - Config: model selection, auth, API method, deployment
   - Deep interview (8 rounds about identity, personality, implementation, etc.)

5. **Review the generated spec:**
   - Spec saved to `specs/agent-spec-{your-agent-name}.md`
   - Approve or request changes

6. **Get your agent built:**
   - Complete project created in a sibling directory: `../{your-agent-name}/`
   - Includes code, configuration, and deployment instructions

## What Gets Built

Depending on your architecture choices, you get:

### Option 1: Full-Stack (Postgres + Web + Hetzner)
- PostgreSQL database with asyncpg
- Next.js web frontend
- Clerk authentication
- Composio integrations (Calendar, Asana, Slack)
- Hetzner deployment setup via Tailscale

### Option 2: Lightweight (SQLite + Telegram)
- SQLite or JSON storage
- Telegram bot interface
- Simple deployment
- Single-purpose focused

### Option 3: Supabase MCP
- Managed PostgreSQL via Supabase
- MCP server integration for database operations
- Rapid prototyping
- No database management overhead

## Documentation

All documentation is in `docs/`:

- **`docs/reference-prompts/`** - Example system prompts showing best practices
  - `claude-code-system-prompt.md` - **Read this first** - Gold standard multi-tool orchestration
  - `aristotle-companion.md` - Conversational personality patterns
  - `perplexity.md` - Search/research agent patterns

- **`docs/agent-sdk/`** - Claude Agent SDK documentation
  - `02-python-reference.md` - Python API reference
  - `04-mcp-servers.md` - MCP tool servers
  - `08-custom-tools.md` - Custom tool patterns

- **`docs/templates/`** - Architecture templates
  - `postgres-web-hetzner.md` - Full-stack template
  - `sqlite-telegram.md` - Lightweight template
  - `supabase-mcp.md` - Supabase MCP template

## Reference Implementations

The `/build-agent` command references working agent implementations to understand patterns and best practices. These are used internally as templates but aren't included in this repository.

## Example Output

After running `/build-agent`, you'll have:

```
../{your-agent}/
├── agent.py              # Main agent code with Claude SDK
├── tools.py              # Custom tool implementations
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── README.md             # Agent-specific documentation
└── ...                   # Additional files based on architecture
```

## Tips

- **Read reference prompts first** - They show what good system prompts look like
- **Be specific during interview** - The more detail you provide, the better the agent
- **Start simple** - You can always add complexity later
- **Use Supabase MCP** - For quick prototyping without database management

## Troubleshooting

**Command not found:**
- Make sure you're in the `agent_builder` directory when you run `claude`
- The `.claude/commands/` folder must exist with `build-agent.md`

**MCP connection issues:**
- Check `.mcp.json` exists
- Run `claude /mcp` to configure Supabase authentication

**Build fails:**
- Check the generated spec in `specs/` for issues
- Review error messages and adjust your requirements

## Contributing

This is a personal tool but feel free to fork and adapt for your needs.

## License

MIT
