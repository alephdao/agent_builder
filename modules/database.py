"""SQLite database for storing prompt references and examples."""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PromptDatabase:
    """Manages SQLite database for prompt documents and references."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database tables."""
        with self._get_conn() as conn:
            # Prompt documents table - stores references to system prompts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompt_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    github_url TEXT,
                    local_path TEXT,
                    category TEXT,
                    priority INTEGER DEFAULT 0,
                    source_updated_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Add columns if they don't exist (for existing databases)
            try:
                conn.execute("ALTER TABLE prompt_documents ADD COLUMN priority INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
            try:
                conn.execute("ALTER TABLE prompt_documents ADD COLUMN source_updated_at TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Conversations table - chat history
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    agent_name TEXT,
                    status TEXT DEFAULT 'active'
                )
            """)

            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            # Generated prompts table - prompts created by the builder
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generated_prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            conn.commit()

    # ============ Prompt Documents ============

    def add_document(
        self,
        name: str,
        description: str = None,
        github_url: str = None,
        local_path: str = None,
        category: str = None,
        priority: int = 0,
        source_updated_at: str = None
    ) -> int:
        """Add a prompt document reference.

        Args:
            priority: Higher = more important. 100 = primary reference, 90 = secondary, etc.
            source_updated_at: When the original prompt source was last updated (ISO format)
        """
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO prompt_documents
                (name, description, github_url, local_path, category, priority, source_updated_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, description, github_url, local_path, category, priority, source_updated_at, now, now))
            conn.commit()
            return cursor.lastrowid

    def get_document(self, name: str) -> Optional[dict]:
        """Get a document by name."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM prompt_documents WHERE name = ?", (name,)
            ).fetchone()
            return dict(row) if row else None

    def list_documents(self, category: str = None, order_by_priority: bool = True) -> list[dict]:
        """List all documents, optionally filtered by category."""
        with self._get_conn() as conn:
            if category:
                order = "priority DESC, name" if order_by_priority else "name"
                rows = conn.execute(
                    f"SELECT * FROM prompt_documents WHERE category = ? ORDER BY {order}",
                    (category,)
                ).fetchall()
            else:
                order = "priority DESC, category, name" if order_by_priority else "category, name"
                rows = conn.execute(
                    f"SELECT * FROM prompt_documents ORDER BY {order}"
                ).fetchall()
            return [dict(row) for row in rows]

    def update_document(self, name: str, **kwargs) -> bool:
        """Update document fields."""
        allowed = {"description", "github_url", "local_path", "category", "priority", "source_updated_at"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False

        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE prompt_documents SET {set_clause} WHERE name = ?",
                (*updates.values(), name)
            )
            conn.commit()
            return True

    def delete_document(self, name: str) -> bool:
        """Delete a document reference."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM prompt_documents WHERE name = ?", (name,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def read_document_content(self, name: str) -> Optional[str]:
        """Read the actual content of a document from its local path."""
        doc = self.get_document(name)
        if not doc or not doc.get("local_path"):
            return None

        path = Path(doc["local_path"])
        if path.exists():
            return path.read_text()
        return None

    # ============ Conversations ============

    def create_conversation(self, session_id: str, agent_name: str = None) -> int:
        """Create a new conversation."""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO conversations (session_id, started_at, agent_name, status)
                VALUES (?, ?, ?, 'active')
            """, (session_id, now, agent_name))
            conn.commit()
            return cursor.lastrowid

    def end_conversation(self, conversation_id: int):
        """Mark conversation as ended."""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE conversations SET ended_at = ?, status = 'completed'
                WHERE id = ?
            """, (now, conversation_id))
            conn.commit()

    def get_active_conversation(self, session_id: str) -> Optional[dict]:
        """Get active conversation for a session."""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT * FROM conversations
                WHERE session_id = ? AND status = 'active'
                ORDER BY id DESC LIMIT 1
            """, (session_id,)).fetchone()
            return dict(row) if row else None

    # ============ Messages ============

    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        """Add a message to a conversation."""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO messages (conversation_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (conversation_id, role, content, now))
            conn.commit()
            return cursor.lastrowid

    def get_messages(self, conversation_id: int, limit: int = None) -> list[dict]:
        """Get messages for a conversation."""
        with self._get_conn() as conn:
            query = """
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY id ASC
            """
            if limit:
                query += f" LIMIT {limit}"
            rows = conn.execute(query, (conversation_id,)).fetchall()
            return [dict(row) for row in rows]

    # ============ Generated Prompts ============

    def save_generated_prompt(
        self,
        name: str,
        content: str,
        conversation_id: int = None,
        metadata: str = None
    ) -> int:
        """Save a generated prompt."""
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT INTO generated_prompts (conversation_id, name, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, name, content, metadata, now))
            conn.commit()
            return cursor.lastrowid

    def get_generated_prompt(self, prompt_id: int) -> Optional[dict]:
        """Get a generated prompt by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM generated_prompts WHERE id = ?", (prompt_id,)
            ).fetchone()
            return dict(row) if row else None

    def list_generated_prompts(self) -> list[dict]:
        """List all generated prompts."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM generated_prompts ORDER BY created_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]
