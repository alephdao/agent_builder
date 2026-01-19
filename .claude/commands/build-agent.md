---
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, AskUserQuestion, TodoWrite
description: Build a complete AI agent from scratch. Interviews you in-depth, creates a detailed spec, then builds the full project.
---

# Build Agent

Build a complete AI agent through structured discovery and automated project generation.

## Before You Start

**Read the CLAUDE.md file first** to understand where all the reference materials are located.

## Key Directories

All documentation is in `docs/`:

```
docs/
├── reference-prompts/      # Example system prompts (READ ALL OF THESE)
│   ├── claude-code-system-prompt.md   # Gold standard - read this first
│   ├── aristotle-companion.md         # Conversational personality
│   ├── perplexity.md                  # Search/research agent
│   └── ... (others)
├── agent-sdk/              # Claude Agent SDK documentation
│   ├── 00-overview.md
│   ├── 02-python-reference.md
│   └── ... (others)
└── templates/              # Architecture templates
    ├── postgres-web-hetzner.md   # Full-stack (Smithers pattern)
    └── sqlite-telegram.md        # Lightweight (Telegram bot pattern)
```

## Reference Implementations

**IMPORTANT:** Before building, read these reference implementation patterns:

1. **Full-Stack Pattern** (Postgres + Web + Hetzner + Composio)
   - Patterns: `docs/reference-implementations/smithers-patterns.md`
   - Template: `docs/templates/postgres-web-hetzner.md`

2. **Telegram Bot Pattern** (Lightweight: SQLite + Telegram)
   - Patterns: `docs/reference-implementations/telegram-bot-patterns.md`
   - Template: `docs/templates/sqlite-telegram.md`

## Workflow

### Phase 1: Architecture Selection

**Use AskUserQuestion to determine the template.** Ask these 4 questions FIRST:

```
Question 1: "What interface will users interact with?"
Header: "Interface"
Options:
- "Telegram bot" - Simple messaging interface, single-purpose
- "Web app" - Custom frontend, multi-feature dashboard
- "CLI only" - Command-line tool, developer-focused

Question 2: "What database do you need?"
Header: "Database"
Options:
- "SQLite (committed)" - Simple, portable, version controlled
- "SQLite (local only)" - Simple, not committed, .gitignore'd
- "Postgres (local)" - Scalable, run locally for development
- "Postgres (Hetzner)" - Production-ready, hosted on Hetzner server

Question 3: "Will this agent need external integrations?"
Header: "Integrations"
Options:
- "None" - Self-contained, no external APIs
- "Composio" - Google Calendar, Asana, Slack, etc. via Composio
- "Custom APIs" - Direct API integrations (you'll implement)

Question 4: "Where will this agent run?"
Header: "Deployment"
Options:
- "Local only" - Development/personal use
- "Hetzner server" - Production deployment via Tailscale
```

**Based on answers, read the matching template:**
- Telegram + SQLite → Read `docs/templates/sqlite-telegram.md`
- Web + Postgres + Hetzner → Read `docs/templates/postgres-web-hetzner.md`

### Phase 2: Deep Interview

**Before interviewing, read the reference prompts in `docs/reference-prompts/` to understand good prompt patterns.**

Interview the user continuously using AskUserQuestion until you have complete understanding. Questions must be NON-OBVIOUS.

#### Round 1: Core Identity (2-3 questions)
```
"What specific problem does this agent solve that existing tools don't?"
"Who is the primary user and what's their technical level?"
"In one sentence, what should users say when describing this agent to others?"
```

#### Round 2: Personality & Tone (2-3 questions)
```
"When the agent doesn't know something, should it admit uncertainty or make a best guess?"
"Should responses be concise (Twitter-length) or detailed (documentation-style)?"
"Any personality traits to emphasize? (e.g., encouraging, blunt, formal, playful)"
```

#### Round 3: Technical Implementation (3-4 questions)
```
"When reading from the database, should results be cached or always fresh?"
"If a tool fails mid-execution, should the agent retry, report the error, or use a fallback?"
"Should the agent handle multiple requests simultaneously, or queue them?"
"What's the maximum response time users will tolerate?"
```

#### Round 4: Data & State (2-3 questions)
```
"What data needs to persist between conversations?"
"Should conversation history be kept forever, or pruned after N days/messages?"
"If the agent stores user data, what's the retention policy?"
```

#### Round 5: Tools & Capabilities (2-4 questions)
```
"What actions should the agent be able to take?"
"Which actions are read-only vs. have side effects?"
"Should any tools require explicit user confirmation before executing?"
```

#### Round 6: Edge Cases & Safety (2-3 questions)
```
"What should the agent do if the user asks something outside its scope?"
"Are there topics or actions the agent should NEVER engage with?"
"If the user provides contradictory instructions, how should the agent handle it?"
```

#### Round 7: User Experience (2-3 questions)
```
"When responses are long, should the agent chunk them, summarize, or ask if user wants more?"
"Should the agent proactively offer suggestions, or only respond to explicit requests?"
"How should the agent handle ambiguous requests?"
```

#### Round 8: Examples (1-2 questions)
```
"Describe an ideal interaction - what does the user say, what does the agent do?"
"What's a tricky edge case the agent should handle gracefully?"
```

### Phase 3: Generate Spec

Write a detailed spec to: `specs/agent-spec-{slug}.md`

**Spec Structure:**

```markdown
# Agent Spec: {Name}

Generated: {timestamp}
Template: {selected template}

## Overview
- **Name**: {name}
- **Slug**: {slug}
- **Description**: {1-2 sentences}
- **Interface**: {Telegram / Web / CLI}
- **Database**: {SQLite / Postgres}
- **Deployment**: {Local / Hetzner}
- **Integrations**: {None / Composio / Custom}

## Architecture Decisions
{Details based on Phase 1 answers}

## System Prompt Requirements
{Based on Phase 2 interview}

## Technical Details
{Error handling, performance, data retention}

## Interview Summary
{Key insights from interview}
```

### Phase 4: User Review

Tell the user:
```
I've created a detailed spec at: specs/agent-spec-{slug}.md

Please review it. Say "build it" when ready, or tell me what to change.
```

### Phase 5: Build

**Only proceed after user explicitly confirms.**

1. Read the matching template from `docs/templates/`
2. Read the reference implementation patterns:
   - For Postgres/Web: `docs/reference-implementations/smithers-patterns.md`
   - For Telegram: `docs/reference-implementations/telegram-bot-patterns.md`
3. Create project in sibling directory: `../{slug}/`
4. Generate all files based on spec, template, and reference patterns

**Confirm completion:**
```
Your agent "{name}" has been created at:
../{slug}/

Next steps:
1. cd ../{slug}
2. {setup instructions based on template}
```

## Guidelines

- Ask 2-4 questions at a time using AskUserQuestion
- Build on previous answers - each round should go deeper
- Questions must be non-obvious - things the user hasn't considered
- Don't stop early - keep interviewing until comprehensive understanding
- Read reference prompts before generating the system prompt
