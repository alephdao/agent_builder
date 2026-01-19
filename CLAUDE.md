# Agent Prompt Builder

An AI agent that helps you build AI agents. It guides you through a structured discovery process to create comprehensive, effective system prompts.

## Quick Start

```bash
cd /Users/philipgalebach/coding-projects/_agents/agent_prompt_builder
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## How It Works

1. **Describe your agent** - Tell it what kind of agent you want to build
2. **Answer questions** - The builder asks clarifying questions about:
   - Core identity & purpose
   - Personality & character
   - Tools & capabilities
   - Context & knowledge needed
   - Commands & interactions
   - Output format & style
   - Safety & guardrails
   - Examples
3. **Get your prompt** - The builder generates a complete system prompt

## Commands

- `/list` - List reference prompts in the database
- `/view [name]` - View a specific reference prompt
- `/add` - Add a new reference prompt to the database
- `/draft` - Generate a draft prompt from the conversation
- `/new` - Start a new conversation
- `/history` - Show conversation history
- `/quit` - Exit

## Database

Uses SQLite to store:
- **prompt_documents** - Reference prompts with name, description, GitHub URL, local path, category
- **conversations** - Chat sessions
- **messages** - Message history
- **generated_prompts** - Prompts created by the builder

## Adding Reference Prompts

Use `/add` to interactively add prompts, or use the database module directly:

```python
from modules.database import PromptDatabase

db = PromptDatabase("data/prompts.db")
db.add_document(
    name="smithers-agent",
    description="Personal AI assistant with Asana/Calendar integration",
    github_url="https://github.com/user/repo/blob/main/prompts/smithers.md",
    local_path="/path/to/smithers.md",
    category="assistant"
)
```

## Architecture

```
agent_prompt_builder/
├── main.py              # CLI entry point
├── prompts/
│   └── system_prompt.md # Builder agent's system prompt
├── modules/
│   ├── database.py      # SQLite for prompts & conversations
│   └── conversation.py  # Conversation manager
└── data/
    └── prompts.db       # SQLite database (created on first run)
```

## Claude Agent SDK

Uses the Claude Agent SDK for conversation. Requires either:
- OAuth credentials in `~/.claude/` (from `claude` CLI)
- Or `ANTHROPIC_API_KEY` environment variable
