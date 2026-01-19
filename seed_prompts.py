#!/usr/bin/env python3
"""Seed the database with reference prompts from the _agents directory."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.database import PromptDatabase

# Known prompt locations in the _agents directory
AGENTS_DIR = Path("/Users/philipgalebach/coding-projects/_agents")

# Reference prompts with metadata
# Priority levels:
#   100 = PRIMARY REFERENCE (gold standard)
#    95 = PRIMARY REFERENCE (important tools/standards)
#    90 = SECONDARY REFERENCE (excellent examples)
#    85 = CONVERSATIONAL COMPANION (excellent dialogue patterns)
#    80 = CLAUDE MODELS (model reference prompts)
#    70 = OTHER REFERENCES (other LLM examples)

REFERENCE_PROMPTS = [
    # PRIMARY REFERENCE - Claude Code System Prompt (Gold Standard)
    {
        "name": "claude-code-system-prompt",
        "description": "The official Claude Code CLI system prompt - THE GOLD STANDARD for agent prompts",
        "github_url": "https://github.com/matthew-lim-matthew-lim/claude-code-system-prompt/blob/main/claudecode.md",
        "local_path": str(PROJECT_ROOT / "prompts/references/claude-code-system-prompt.md"),
        "category": "claude-code",
        "priority": 100,
        "source_updated_at": "2025-01-15",
    },
    # PRIMARY REFERENCE - Claude Code Tools
    {
        "name": "claude-code-tools",
        "description": "Claude Code's tool definitions - reference for how to define agent tools",
        "github_url": "https://gist.github.com/wong2/e0f34aac66caf890a332f7b6f9e2ba8f",
        "local_path": str(PROJECT_ROOT / "prompts/references/claude-code-tools.md"),
        "category": "claude-code",
        "priority": 95,
        "source_updated_at": "2025-01-10",
    },
    # SECONDARY REFERENCE - Perplexity
    {
        "name": "perplexity",
        "description": "Perplexity AI search assistant prompt - excellent example of search-focused agent",
        "github_url": "https://github.com/jujumilk3/leaked-system-prompts/blob/main/perplexity.ai_20250112.md",
        "local_path": str(PROJECT_ROOT / "prompts/references/perplexity.md"),
        "category": "search",
        "priority": 90,
        "source_updated_at": "2025-01-12",
    },
    # CONVERSATIONAL COMPANION - Aristotle (Excellent dialogue patterns)
    {
        "name": "aristotle-companion",
        "description": "Philosophical conversational companion - excellent example of Socratic dialogue, persona, and conversational discipline",
        "local_path": str(PROJECT_ROOT / "prompts/references/aristotle-companion.md"),
        "category": "companion",
        "priority": 85,
        "source_updated_at": "2026-01-17",
    },
    # CLAUDE MODELS
    {
        "name": "claude-opus-4.5",
        "description": "Claude Opus 4.5 model capabilities and system prompt reference",
        "local_path": str(PROJECT_ROOT / "prompts/references/claude-opus-4.5.md"),
        "category": "claude-models",
        "priority": 80,
        "source_updated_at": "2025-01-17",
    },
    {
        "name": "claude-sonnet-4.5",
        "description": "Claude Sonnet 4.5 model capabilities and system prompt reference",
        "local_path": str(PROJECT_ROOT / "prompts/references/claude-sonnet-4.5.md"),
        "category": "claude-models",
        "priority": 80,
        "source_updated_at": "2025-01-17",
    },
    {
        "name": "claude-haiku-4.5",
        "description": "Claude Haiku 4.5 model capabilities and system prompt reference",
        "local_path": str(PROJECT_ROOT / "prompts/references/claude-haiku-4.5.md"),
        "category": "claude-models",
        "priority": 80,
        "source_updated_at": "2025-01-17",
    },
    # OTHER LLM REFERENCES
    {
        "name": "chatgpt5",
        "description": "ChatGPT 5 system prompt - reference for alternative LLM approach",
        "local_path": str(PROJECT_ROOT / "prompts/references/chatgpt5.md"),
        "category": "other-llms",
        "priority": 70,
        "source_updated_at": "2025-01-15",
    },
    {
        "name": "grok3",
        "description": "Grok 3 system prompt - Elon Musk's AI assistant reference",
        "local_path": str(PROJECT_ROOT / "prompts/references/grok3.md"),
        "category": "other-llms",
        "priority": 70,
        "source_updated_at": "2025-01-15",
    },
    {
        "name": "openai-deep-research",
        "description": "OpenAI Deep Research mode system prompt - research-focused AI approach",
        "local_path": str(PROJECT_ROOT / "prompts/references/openai-deep-research.md"),
        "category": "other-llms",
        "priority": 70,
        "source_updated_at": "2025-01-15",
    },
    {
        "name": "gemini-cli",
        "description": "Google Gemini CLI system prompt - multimodal AI reference",
        "local_path": str(PROJECT_ROOT / "prompts/references/gemini-cli.md"),
        "category": "other-llms",
        "priority": 70,
        "source_updated_at": "2025-01-15",
    },
    # SMITHERS AGENT (Local)
    {
        "name": "smithers-agent",
        "description": "Personal AI assistant with Asana, Calendar, and database integration",
        "local_path": str(AGENTS_DIR / "smithers/apps/agent/prompts/smithers.md"),
        "category": "assistant",
        "priority": 60,
    },
    # SPANISH TRANSLATOR (Local)
    {
        "name": "spanish-translator",
        "description": "Argentine Spanish translator with conversation context",
        "local_path": str(AGENTS_DIR / "spanish-translator/telegram_bot/prompts/system_prompt.md"),
        "category": "translator",
        "priority": 60,
    },
    # MEETING ANALYZER (Local)
    {
        "name": "meeting-analyzer",
        "description": "Extracts action items and notes from meeting transcripts",
        "local_path": str(AGENTS_DIR / "apps/meeting-analyzer/prompts/analyzer.md"),
        "category": "analyzer",
        "priority": 60,
    },
    # AGENT BUILDER SELF (Meta)
    {
        "name": "agent-builder-self",
        "description": "This agent's own system prompt (meta!)",
        "local_path": str(PROJECT_ROOT / "prompts/system_prompt.md"),
        "category": "builder",
        "priority": 50,
    },
]


def main():
    db = PromptDatabase(PROJECT_ROOT / "data" / "prompts.db")

    added = 0
    skipped = 0

    print("Seeding database with reference prompts...\n")

    for prompt in REFERENCE_PROMPTS:
        # Check if path exists
        path = Path(prompt["local_path"])
        if not path.exists():
            print(f"  SKIP: {prompt['name']:40s} (file not found)")
            skipped += 1
            continue

        # Check if already exists
        existing = db.get_document(prompt["name"])
        if existing:
            print(f"  SKIP: {prompt['name']:40s} (already exists)")
            skipped += 1
            continue

        # Add to database
        db.add_document(**prompt)
        print(f"  ADD:  {prompt['name']:40s} [priority={prompt.get('priority', 0)}]")
        added += 1

    print(f"\n{'='*70}")
    print(f"Summary: Added {added}, Skipped {skipped}")
    print(f"{'='*70}\n")

    # List all prompts ordered by priority
    print("All reference prompts (ordered by priority):\n")
    all_docs = db.list_documents(order_by_priority=True)

    current_category = None
    for doc in all_docs:
        category = doc.get('category', 'none')
        if category != current_category:
            current_category = category
            print(f"\n{category.upper()}:")

        priority = doc.get('priority', 0)
        print(f"  {doc['name']:40s} (priority={priority:3d})")


if __name__ == "__main__":
    main()
