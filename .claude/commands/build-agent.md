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
├── templates/              # Architecture templates
│   ├── postgres-web-hetzner.md   # Full-stack (Smithers pattern)
│   └── sqlite-telegram.md        # Lightweight (Telegram bot pattern)
└── model-selection-guide.md   # Model comparison (Haiku/Sonnet/Opus)
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

**Use AskUserQuestion to determine the template.** Ask questions in TWO rounds:

#### Round 1A: Core Architecture (4 questions)

```
Question 1: "What interface will users interact with?"
Header: "Interface"
Options:
- "Telegram bot" - Simple messaging interface, single-purpose
- "Web app" - Custom frontend, multi-feature dashboard
- "CLI only" - Command-line tool, developer-focused

Question 2: "What type of data storage?"
Header: "Storage"
Options:
- "JSON files" - Simplest, human-readable, version-controlled
- "SQLite (local)" - File-based SQL, portable, gitignored
- "Postgres (local)" - Full SQL database, local development
- "Supabase" - Managed Postgres, no infrastructure setup

Question 3: "What kind of data will this agent store?"
Header: "Data Type"
Options:
- "Conversations only" - Just chat history
- "User preferences" - Settings, configs, user-specific data
- "Rich documents" - Meetings, notes, health records, etc.
- "Multiple types" - Combination of above

Question 4: "Will this agent need external integrations?"
Header: "Integrations"
Options:
- "None" - Self-contained, no external APIs
- "Composio" - Calendar, Asana, Slack via OAuth
- "Custom APIs" - Direct API integrations you'll build
```

#### Round 1B: Deployment & Auth (4 questions)

**NOTE:** Before asking Question 5, read `docs/model-selection-guide.md` to understand model tradeoffs.

```
Question 5: "Which Claude model should power this agent?"
Header: "Model"
Options:
- "Haiku (claude-haiku-4-5-20251001)" - Lightning fast, lower cost, less capable. Best for: simple tasks, high volume, speed-critical
- "Sonnet (claude-sonnet-4-5-20250929)" - Balanced speed/intelligence/cost. Best for: most agents, coding, general purpose (Recommended)
- "Opus (claude-opus-4-5-20251101)" - Highest intelligence, slower, premium cost. Best for: complex reasoning, critical decisions

Question 6: "How will users authenticate?"
Header: "Auth"
Options:
- "None" - Open access, no authentication
- "Telegram user ID" - Built-in Telegram auth (for bots)
- "Clerk" - Web auth with OAuth providers (Google, GitHub, etc.)
- "Custom" - You'll implement your own auth

Question 7: "How will Claude be accessed?"
Header: "Claude API"
Options:
- "API Key" - Direct Anthropic API with your key (you pay per token)
- "OAuth Token" - User's Claude subscription token (they pay, via Claude.ai login)

Question 8: "Where will this agent run?"
Header: "Deployment"
Options:
- "Local only" - Development/personal use
- "Hetzner server" - Production VPS via Tailscale
- "Docker" - Containerized deployment
```

**Based on answers, read the matching template:**
- Telegram + JSON/SQLite → Read `docs/templates/sqlite-telegram.md` + `docs/reference-implementations/telegram-bot-patterns.md`
- Web + Postgres/Supabase → Read `docs/templates/postgres-web-hetzner.md` + `docs/reference-implementations/smithers-patterns.md`

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

## Architecture Decisions

### Interface & Frontend
- **Interface**: {Telegram / Web / CLI}
- **Frontend Details**: {specific framework, features}

### Data & Storage
- **Storage Type**: {JSON / SQLite / Postgres / Supabase}
- **Data Types**: {conversations, preferences, documents, etc.}
- **Retention Policy**: {how long data is kept}

### Integrations & Tools
- **Integration Method**: {None / Composio / Custom}
- **Specific Integrations**: {Calendar, Asana, Slack, etc.}
- **Custom Tools**: {list of custom tools needed}

### Model & API
- **Claude Model**: {Haiku / Sonnet / Opus}
- **Model ID**: {claude-XXX-X-X-XXXXXXXX}
- **API Method**: {API Key / OAuth Token}
- **Rationale**: {why this model was chosen}

### Authentication & Security
- **Auth Method**: {None / Telegram / Clerk / Custom}
- **User Management**: {single-user / multi-user}
- **Security Requirements**: {data privacy, access control}

### Deployment
- **Environment**: {Local / Hetzner / Docker}
- **Infrastructure**: {VPS, containers, systemd}
- **Scaling Considerations**: {single-instance / load-balanced}

## System Prompt Requirements
{Based on Phase 2 interview - personality, tone, capabilities}

## Technical Implementation Details
- **Error Handling**: {retry logic, fallbacks, user messaging}
- **Performance**: {caching, rate limits, timeouts}
- **Data Retention**: {cleanup policies, archiving}
- **Logging & Monitoring**: {what to log, where to send logs}

## User Experience Flow
{Example interactions showing typical user journeys}

## Edge Cases & Safety
{Boundary conditions, error scenarios, safety guardrails}

## Interview Summary
{Key insights and decisions from interview rounds}
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
