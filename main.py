#!/usr/bin/env python3
"""Agent Prompt Builder - CLI for building agent system prompts interactively."""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import sys
import logging
from pathlib import Path

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.database import PromptDatabase
from modules.conversation import ConversationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "sonnet")
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = PROJECT_ROOT / "prompts"


def load_system_prompt() -> str:
    """Load the system prompt from file."""
    prompt_path = PROMPTS_DIR / "system_prompt.md"
    if not prompt_path.exists():
        return "You are an AI agent prompt builder. Help users design system prompts for AI agents."
    return prompt_path.read_text()


class AgentPromptBuilder:
    """Main application class for the agent prompt builder."""

    def __init__(self):
        self.db = PromptDatabase(DATA_DIR / "prompts.db")
        self.conversation = ConversationManager(self.db)
        self.client: ClaudeSDKClient | None = None
        self.system_prompt = load_system_prompt()
        self.improve_target_path: Path | None = None

    async def initialize_client(self):
        """Initialize the Claude SDK client."""
        options = ClaudeAgentOptions(
            cwd=str(PROJECT_ROOT),
            system_prompt=self.system_prompt,
            model=CLAUDE_MODEL,
            permission_mode="bypassPermissions",
            max_turns=10,
        )

        self.client = ClaudeSDKClient(options=options)
        await self.client.__aenter__()
        logger.info("Claude SDK client initialized")

    async def cleanup(self):
        """Cleanup resources."""
        if self.client:
            await self.client.__aexit__(None, None, None)

    def handle_command(self, cmd: str) -> str | None:
        """Handle special commands. Returns response or None to continue to Claude."""
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if command == "/help":
            return """
Available Commands:
  /new             - Start a new prompt from scratch
  /improve [path]  - Improve an existing prompt by analyzing a repository
  /list            - List available reference prompts
  /view [name]     - View content of a reference prompt
  /add             - Add a reference prompt to the database
  /draft           - Ask Claude to generate a draft prompt
  /history         - Show conversation history
  /quit            - Exit the application

Examples:
  /improve /Users/me/my-agent
  /view claude-code-system-prompt
"""

        elif command == "/list":
            docs = self.conversation.list_reference_prompts()
            if not docs:
                return "No reference prompts in database. Use /add to add some."
            lines = ["Reference Prompts:"]
            for doc in docs:
                cat = f"[{doc['category']}]" if doc.get("category") else ""
                lines.append(f"  - {doc['name']} {cat}")
                if doc.get("description"):
                    lines.append(f"      {doc['description']}")
            return "\n".join(lines)

        elif command == "/view":
            if not arg:
                return "Usage: /view [prompt_name]"
            content = self.conversation.get_reference_prompt_content(arg)
            if content:
                return f"=== {arg} ===\n{content}"
            else:
                doc = self.db.get_document(arg)
                if doc:
                    return f"Found '{arg}' but cannot read content. Path: {doc.get('local_path')}"
                return f"Prompt '{arg}' not found. Use /list to see available prompts."

        elif command == "/add":
            return self._interactive_add_prompt()

        elif command == "/new":
            self.conversation.new_conversation()
            self.improve_target_path = None
            return "Started new conversation. What kind of agent would you like to build?"

        elif command == "/improve":
            if not arg:
                return "Usage: /improve [path_to_repo]\nExample: /improve /Users/me/my-agent"

            target_path = Path(arg).expanduser().resolve()
            if not target_path.exists():
                return f"Path does not exist: {target_path}"
            if not target_path.is_dir():
                return f"Path is not a directory: {target_path}"

            # Store the target path for context
            self.improve_target_path = target_path
            self.conversation.new_conversation()

            # Return IMPROVE signal to trigger the improve workflow
            return f"IMPROVE:{target_path}"

        elif command == "/history":
            messages = self.conversation.get_messages()
            if not messages:
                return "No messages in current conversation."
            lines = ["Conversation History:"]
            for msg in messages:
                role = "You" if msg["role"] == "user" else "Agent"
                preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                lines.append(f"  [{role}] {preview}")
            return "\n".join(lines)

        elif command == "/quit" or command == "/exit":
            return "QUIT"

        # /draft and /save are handled by Claude
        return None

    def _interactive_add_prompt(self) -> str:
        """Interactively add a prompt reference."""
        print("\n--- Add Reference Prompt ---")
        name = input("Name (unique identifier): ").strip()
        if not name:
            return "Cancelled - name is required."

        description = input("Description (optional): ").strip() or None
        github_url = input("GitHub URL (optional): ").strip() or None
        local_path = input("Local file path (optional): ").strip() or None
        category = input("Category (optional, e.g., 'assistant', 'coder', 'analyzer'): ").strip() or None

        try:
            self.db.add_document(
                name=name,
                description=description,
                github_url=github_url,
                local_path=local_path,
                category=category
            )
            return f"Added prompt reference: {name}"
        except Exception as e:
            return f"Error adding prompt: {e}"

    async def chat(self, user_input: str) -> str:
        """Send a message to Claude and get response."""
        # Build context with conversation history
        history = self.conversation.get_context_for_claude(limit=10)

        # Include reference to available prompts
        docs = self.conversation.list_reference_prompts()
        prompt_list = ", ".join(d["name"] for d in docs) if docs else "none available"

        # Add improve mode context if set
        improve_context = ""
        if self.improve_target_path:
            improve_context = f"""
=== IMPROVE MODE ACTIVE ===
Target repository: {self.improve_target_path}
You are in IMPROVE mode. Explore this repository to understand:
- The existing system prompt (look in prompts/, .claude/, or root)
- Database schema (look for .db files, models.py, schema.sql)
- Available tools (look for tools/, functions, API handlers)
- Integrations (look for API clients, config files)
Then use AskUserQuestion to gather improvement goals.
===========================
"""

        full_prompt = f"""Available reference prompts in database: {prompt_list}
{improve_context}
Previous conversation:
{history}

User: {user_input}"""

        # Save user message
        self.conversation.add_message("user", user_input)

        # Query Claude
        await self.client.query(full_prompt)

        # Collect response
        response_text = ""
        async for sdk_message in self.client.receive_response():
            if isinstance(sdk_message, AssistantMessage):
                for block in sdk_message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text

        # Save assistant response
        self.conversation.add_message("assistant", response_text)

        return response_text

    async def run(self):
        """Main run loop."""
        print("\n" + "=" * 60)
        print("  Agent Prompt Builder")
        print("  Build AI agent system prompts interactively")
        print("=" * 60)
        print("\nType /help for commands, or describe the agent you want to build.\n")

        await self.initialize_client()

        try:
            while True:
                try:
                    user_input = input("\nYou: ").strip()
                except EOFError:
                    break

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    result = self.handle_command(user_input)
                    if result == "QUIT":
                        print("\nGoodbye!")
                        break
                    if result and result.startswith("IMPROVE:"):
                        # Trigger improve mode with automatic exploration
                        target_path = result.split(":", 1)[1]
                        print(f"\n=== Improve Mode ===")
                        print(f"Analyzing repository: {target_path}")
                        print("Exploring codebase to understand existing system prompt, tools, and integrations...\n")

                        # Send initial improve message to Claude
                        improve_prompt = f"I want to improve the system prompt for the agent at {target_path}. Please explore the repository to understand the existing prompt, database schema, tools, and integrations. Then use AskUserQuestion to ask me what aspects I want to improve."
                        try:
                            response = await self.chat(improve_prompt)
                            print(f"\nAgent: {response}")
                        except Exception as e:
                            logger.error(f"Error in improve mode: {e}", exc_info=True)
                            print(f"\nError: {e}")
                        continue
                    if result:
                        print(f"\n{result}")
                        continue

                # Chat with Claude
                try:
                    response = await self.chat(user_input)
                    print(f"\nAgent: {response}")
                except Exception as e:
                    logger.error(f"Error in chat: {e}", exc_info=True)
                    print(f"\nError: {e}")

        finally:
            await self.cleanup()


async def main():
    """Entry point."""
    app = AgentPromptBuilder()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
