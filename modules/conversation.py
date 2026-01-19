"""Conversation manager for the agent prompt builder."""

import uuid
from typing import Optional
import logging

from .database import PromptDatabase

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversations and integrates with the prompt database."""

    def __init__(self, db: PromptDatabase, session_id: str = None):
        self.db = db
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.conversation_id: Optional[int] = None
        self._ensure_conversation()

    def _ensure_conversation(self):
        """Ensure we have an active conversation."""
        conv = self.db.get_active_conversation(self.session_id)
        if conv:
            self.conversation_id = conv["id"]
        else:
            self.conversation_id = self.db.create_conversation(self.session_id)

    def new_conversation(self, agent_name: str = None) -> int:
        """Start a new conversation."""
        if self.conversation_id:
            self.db.end_conversation(self.conversation_id)
        self.conversation_id = self.db.create_conversation(self.session_id, agent_name)
        return self.conversation_id

    def add_message(self, role: str, content: str):
        """Add a message to current conversation."""
        if not self.conversation_id:
            self._ensure_conversation()
        self.db.add_message(self.conversation_id, role, content)

    def get_messages(self, limit: int = None) -> list[dict]:
        """Get messages from current conversation."""
        if not self.conversation_id:
            return []
        return self.db.get_messages(self.conversation_id, limit)

    def get_context_for_claude(self, limit: int = 10) -> str:
        """Get recent conversation history formatted for Claude context."""
        messages = self.get_messages(limit)
        if not messages:
            return ""

        lines = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content']}")

        return "\n".join(lines)

    def save_prompt(self, name: str, content: str, metadata: str = None) -> int:
        """Save a generated prompt."""
        return self.db.save_generated_prompt(
            name=name,
            content=content,
            conversation_id=self.conversation_id,
            metadata=metadata
        )

    def list_reference_prompts(self, category: str = None) -> list[dict]:
        """List available reference prompts."""
        return self.db.list_documents(category)

    def get_reference_prompt_content(self, name: str) -> Optional[str]:
        """Get content of a reference prompt."""
        return self.db.read_document_content(name)
