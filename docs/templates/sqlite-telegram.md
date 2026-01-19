# Template: SQLite + Telegram Bot

Reference implementation: `/Users/philipgalebach/coding-projects/_agents/spanish-translator/telegram_bot`

Use this template when the user wants:
- Simple SQLite or JSON-file storage (committed to repo or local)
- Telegram bot interface
- Single-purpose agent
- Lightweight deployment
- No web frontend needed

## Directory Structure

```
{agent-name}/
├── bot.py                          # Main entry point
├── requirements.txt                # Dependencies
├── .env.example                    # Configuration template
├── modules/
│   ├── __init__.py
│   ├── conversation.py             # Conversation manager (SQLite or JSON)
│   └── {custom_module}.py          # Agent-specific logic
├── prompts/
│   └── system_prompt.md            # Agent system prompt
├── data/
│   ├── .gitkeep
│   └── {agent}.db                  # SQLite database (or JSON files)
└── CLAUDE.md
```

## Claude Agent SDK Pattern

```python
# bot.py
import asyncio
import os
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from claude_agent_sdk.types import AssistantMessage, TextBlock

PROJECT_ROOT = Path(__file__).parent
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250514")

# Per-user Claude clients (long-lived for conversation continuity)
claude_clients: dict[int, ClaudeSDKClient] = {}

def load_system_prompt() -> str:
    prompt_path = PROJECT_ROOT / "prompts" / "system_prompt.md"
    return prompt_path.read_text()

async def initialize_claude_client() -> ClaudeSDKClient:
    system_prompt = load_system_prompt()

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        system_prompt=system_prompt,
        model=CLAUDE_MODEL,
        permission_mode="bypassPermissions",
        max_turns=5,
    )

    client = ClaudeSDKClient(options=options)
    await client.__aenter__()
    return client

async def get_client_for_user(user_id: int) -> ClaudeSDKClient:
    if user_id not in claude_clients:
        claude_clients[user_id] = await initialize_claude_client()
    return claude_clients[user_id]

async def reset_client_for_user(user_id: int) -> None:
    if user_id in claude_clients:
        await claude_clients[user_id].__aexit__(None, None, None)
        del claude_clients[user_id]
```

## Telegram Bot Pattern

```python
# bot.py (continued)
from modules.conversation import ConversationManager

conversation_manager = ConversationManager(data_dir="./data")

async def process_message(user_id: int, text: str) -> str:
    """Process a message through Claude and return response."""
    client = await get_client_for_user(user_id)

    # Build context from conversation history
    history = conversation_manager.get_messages(user_id, limit=6)
    context_parts = []
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        context_parts.append(f"{role}: {msg['content']}")

    if context_parts:
        full_prompt = f"Previous conversation:\n{chr(10).join(context_parts)}\n\nUser: {text}"
    else:
        full_prompt = text

    # Save user message
    conversation_manager.add_message(user_id, "user", text)

    # Query Claude
    await client.query(full_prompt)

    # Collect response
    response_text = ""
    async for sdk_message in client.receive_response():
        if isinstance(sdk_message, AssistantMessage):
            for block in sdk_message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    # Save assistant response
    conversation_manager.add_message(user_id, "assistant", response_text)

    return response_text

# Telegram handlers
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        "Hello! I'm {Agent Name}.\n\n"
        "{Description of what the agent does}\n\n"
        "Commands:\n"
        "/new - Start a new conversation\n"
        "/history - Show recent messages"
    )

@dp.message(F.text == "/new")
async def cmd_new(message: Message):
    user_id = message.from_user.id
    conversation_manager.new_conversation(user_id)
    await reset_client_for_user(user_id)
    await message.answer("Started a new conversation!")

@dp.message(F.text == "/history")
async def cmd_history(message: Message):
    user_id = message.from_user.id
    messages = conversation_manager.get_messages(user_id, limit=10)

    if not messages:
        await message.answer("No messages in current conversation.")
        return

    history = []
    for msg in messages:
        prefix = "You" if msg["role"] == "user" else "Bot"
        history.append(f"{prefix}: {msg['content'][:100]}...")

    await message.answer("\n\n".join(history))

@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    text = message.text

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        response = await process_message(user_id, text)

        # Handle long responses (Telegram 4000 char limit)
        if len(response) > 4000:
            chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for chunk in chunks:
                await message.answer(chunk)
                await asyncio.sleep(0.3)
        else:
            await message.answer(response)

    except Exception as e:
        await message.answer(f"Error: {str(e)}")

async def main():
    print("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        # Cleanup Claude clients
        for client in claude_clients.values():
            await client.__aexit__(None, None, None)
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## SQLite Conversation Manager

```python
# modules/conversation.py
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

class ConversationManager:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.db_path = self.data_dir / "conversations.db"
        self._init_db()
        self._current_conv: dict[int, str] = {}

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id)")
            conn.commit()

    def _get_current_conversation_id(self, user_id: int) -> str:
        if user_id in self._current_conv:
            return self._current_conv[user_id]

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM conversations WHERE user_id = ? AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1",
                (user_id,)
            ).fetchone()

            if row:
                self._current_conv[user_id] = row[0]
                return row[0]

        return self.new_conversation(user_id)

    def new_conversation(self, user_id: int) -> str:
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # End previous conversation
            conn.execute(
                "UPDATE conversations SET ended_at = ? WHERE user_id = ? AND ended_at IS NULL",
                (now, user_id)
            )
            # Create new conversation
            conn.execute(
                "INSERT INTO conversations (id, user_id, started_at) VALUES (?, ?, ?)",
                (conv_id, user_id, now)
            )
            conn.commit()

        self._current_conv[user_id] = conv_id
        return conv_id

    def add_message(self, user_id: int, role: str, content: str) -> None:
        conv_id = self._get_current_conversation_id(user_id)
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (conv_id, role, content, now)
            )
            conn.commit()

    def get_messages(self, user_id: int, limit: Optional[int] = None) -> list[dict]:
        conv_id = self._get_current_conversation_id(user_id)

        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp"
            if limit:
                query += f" DESC LIMIT {limit}"
                rows = conn.execute(query, (conv_id,)).fetchall()
                rows = list(reversed(rows))
            else:
                rows = conn.execute(query, (conv_id,)).fetchall()

        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]
```

## Alternative: JSON File Storage

```python
# modules/conversation.py (JSON variant)
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

class ConversationManager:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._current_conv: dict[int, str] = {}

    def _get_user_file(self, user_id: int) -> Path:
        return self.data_dir / f"user_{user_id}.json"

    def _load_user_data(self, user_id: int) -> dict:
        file_path = self._get_user_file(user_id)
        if file_path.exists():
            return json.loads(file_path.read_text())
        return {"conversations": []}

    def _save_user_data(self, user_id: int, data: dict) -> None:
        file_path = self._get_user_file(user_id)
        file_path.write_text(json.dumps(data, indent=2))

    def new_conversation(self, user_id: int) -> str:
        data = self._load_user_data(user_id)
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        # End previous conversations
        for conv in data["conversations"]:
            if conv.get("ended") is None:
                conv["ended"] = now

        # Create new conversation
        data["conversations"].append({
            "id": conv_id,
            "started": now,
            "ended": None,
            "messages": []
        })

        self._save_user_data(user_id, data)
        self._current_conv[user_id] = conv_id
        return conv_id

    def add_message(self, user_id: int, role: str, content: str) -> None:
        data = self._load_user_data(user_id)
        conv_id = self._get_current_conversation_id(user_id)

        for conv in data["conversations"]:
            if conv["id"] == conv_id:
                conv["messages"].append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
                break

        self._save_user_data(user_id, data)

    def get_messages(self, user_id: int, limit: Optional[int] = None) -> list[dict]:
        data = self._load_user_data(user_id)
        conv_id = self._get_current_conversation_id(user_id)

        for conv in data["conversations"]:
            if conv["id"] == conv_id:
                messages = conv.get("messages", [])
                if limit:
                    return messages[-limit:]
                return messages

        return []

    def _get_current_conversation_id(self, user_id: int) -> str:
        if user_id in self._current_conv:
            return self._current_conv[user_id]

        data = self._load_user_data(user_id)
        for conv in reversed(data["conversations"]):
            if conv.get("ended") is None:
                self._current_conv[user_id] = conv["id"]
                return conv["id"]

        return self.new_conversation(user_id)
```

## Environment Variables

```bash
# .env

# Telegram
TELEGRAM_TOKEN=123456789:ABC...

# Claude
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-5-20250514

# Optional: Voice transcription
GOOGLE_AI_API_KEY=...

# Storage mode
LOCAL_MODE=true
```

## Requirements

```
aiogram>=3.0.0
claude-agent-sdk
python-dotenv>=1.0.0
```

## System Prompt Pattern

```markdown
# {Agent Name}

You are {name}, a {description}.

## Your Purpose

{What this bot does in 1-2 sentences}

## Guidelines

1. {guideline 1}
2. {guideline 2}
3. {guideline 3}

## Output Format

- {format rule 1}
- {format rule 2}

## Examples

User: {example input}
You: {example output}

## What You Should NEVER Do

- {restriction 1}
- {restriction 2}
```

## Optional: Voice Message Support

```python
# modules/transcription.py
import os
import google.generativeai as genai

def transcribe_audio(audio_path: str) -> str:
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        return "Voice transcription not configured"

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    response = model.generate_content([
        "Transcribe this audio accurately:",
        {"mime_type": "audio/ogg", "data": audio_data}
    ])

    return response.text

# In bot.py, add voice handler:
@dp.message(F.voice)
async def handle_voice(message: Message):
    user_id = message.from_user.id

    # Download voice file
    file = await message.bot.get_file(message.voice.file_id)
    audio_path = f"/tmp/voice_{user_id}.ogg"
    await message.bot.download_file(file.file_path, audio_path)

    # Transcribe
    transcript = transcribe_audio(audio_path)

    # Process through agent
    response = await process_message(user_id, transcript)

    await message.answer(f"Transcript: {transcript}\n\nResponse: {response}")
```

## Deployment Options

### Option 1: Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your tokens

# Run
python bot.py
```

### Option 2: Run on Hetzner (Simple)

```bash
# SSH to server
ssh admin@100.109.131.85

# Clone repo
git clone https://github.com/user/{agent-name}.git /opt/{agent-name}
cd /opt/{agent-name}

# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env

# Create systemd service
sudo tee /etc/systemd/system/{agent-name}.service << EOF
[Unit]
Description={Agent Name} Telegram Bot
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/opt/{agent-name}
Environment=PATH=/opt/{agent-name}/.venv/bin
ExecStart=/opt/{agent-name}/.venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable {agent-name}
sudo systemctl start {agent-name}
```

### Option 3: Remote Storage (SSH to Hetzner)

For storing data on a remote server while running bot locally:

```python
# modules/conversation.py - SSH mode
import subprocess

class ConversationManager:
    def __init__(self, hetzner_host: str, hetzner_user: str, data_dir: str):
        self.hetzner_host = hetzner_host
        self.hetzner_user = hetzner_user
        self.data_dir = data_dir

    def _run_ssh(self, command: str) -> str:
        result = subprocess.run(
            ["ssh", f"{self.hetzner_user}@{self.hetzner_host}", command],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout

    def _load_user_data(self, user_id: int) -> dict:
        file_path = f"{self.data_dir}/user_{user_id}.json"
        output = self._run_ssh(f"cat {file_path} 2>/dev/null || echo '{{}}'")
        return json.loads(output) if output.strip() else {"conversations": []}

    def _save_user_data(self, user_id: int, data: dict) -> None:
        file_path = f"{self.data_dir}/user_{user_id}.json"
        json_str = json.dumps(data, indent=2)
        # Escape for bash
        escaped = json_str.replace("'", "'\"'\"'")
        self._run_ssh(f"echo '{escaped}' > {file_path}")
```

## Key Patterns Summary

| Pattern | Implementation |
|---------|---------------|
| **Database** | SQLite (local) or JSON files |
| **Interface** | Telegram via aiogram |
| **Client Pattern** | Per-user (long-lived for context) |
| **Concurrency** | Async throughout |
| **State** | In-memory cache + persistent storage |
| **Deployment** | systemd service or local |
| **Voice** | Optional Google Gemini transcription |
