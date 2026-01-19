# Telegram Bot: Lightweight Agent Pattern

Reference implementation for SQLite/JSON + Telegram architecture.

## Directory Structure

```
telegram_bot/
├── bot.py                       # Main bot entry point
├── modules/
│   ├── __init__.py
│   ├── conversation_manager.py  # Conversation state management
│   ├── transcribe.py           # Audio transcription (optional)
│   └── utils.py                # Helper functions
├── prompts/
│   └── system_prompt.md        # Claude system prompt
├── data/                       # User data storage (gitignored)
│   ├── conversations/          # Per-user conversation history
│   │   ├── 12345.json
│   │   └── 67890.json
│   └── user_prefs.json         # User preferences
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Core Components

### 1. Bot Entry Point (`bot.py`)

```python
#!/usr/bin/env python3
"""
Telegram Bot with Claude Agent SDK
Lightweight pattern for single-purpose agents
"""

from dotenv import load_dotenv
load_dotenv()

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
)

from modules import ConversationManager

# Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20241022")

PROJECT_ROOT = Path(__file__).parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
DATA_DIR = PROJECT_ROOT / "data"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Per-user Claude clients
claude_clients: dict[int, ClaudeSDKClient] = {}

# Conversation manager
conversation_manager: Optional[ConversationManager] = None


def load_system_prompt() -> str:
    """Load system prompt from prompts/system_prompt.md"""
    prompt_path = PROMPTS_DIR / "system_prompt.md"
    if not prompt_path.exists():
        logger.warning(f"Prompt file not found: {prompt_path}")
        return "You are a helpful AI assistant."

    with open(prompt_path, 'r') as f:
        return f.read()


async def initialize_claude_client() -> ClaudeSDKClient:
    """Initialize Claude SDK client with custom system prompt"""
    system_prompt = load_system_prompt()

    options = ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        system_prompt=system_prompt,
        model=CLAUDE_MODEL,
        permission_mode="bypassPermissions",  # No permission prompts
        max_turns=5,
    )

    client = ClaudeSDKClient(options=options)
    await client.__aenter__()
    return client


async def get_client_for_user(user_id: int) -> ClaudeSDKClient:
    """Get or create Claude client for a specific user"""
    if user_id not in claude_clients:
        logger.info(f"Creating new Claude client for user {user_id}")
        claude_clients[user_id] = await initialize_claude_client()
    return claude_clients[user_id]


async def reset_client_for_user(user_id: int):
    """Reset Claude client for a user (starts fresh conversation)"""
    if user_id in claude_clients:
        logger.info(f"Resetting Claude client for user {user_id}")
        try:
            await claude_clients[user_id].__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error closing client for user {user_id}: {e}")
        del claude_clients[user_id]


async def handle_message(message: Message):
    """Handle incoming text message"""
    user_id = message.from_user.id
    user_text = message.text

    # Handle commands
    if user_text == "/start":
        await message.answer(
            "Hello! I'm your AI assistant. Send me a message to get started."
        )
        return

    if user_text == "/reset":
        await reset_client_for_user(user_id)
        conversation_manager.clear_history(user_id)
        await message.answer("Conversation reset. Starting fresh!")
        return

    try:
        # Get client for this user
        client = await get_client_for_user(user_id)

        # Load conversation history
        history = conversation_manager.get_history(user_id)

        # Send typing indicator
        await message.bot.send_chat_action(
            chat_id=message.chat.id,
            action="typing"
        )

        # Query Claude
        response = await client.query(user_text, history=history)

        # Extract text from response
        response_text = ""
        for block in response.content:
            if isinstance(block, TextBlock):
                response_text += block.text

        # Save to conversation history
        conversation_manager.add_message(user_id, "user", user_text)
        conversation_manager.add_message(user_id, "assistant", response_text)

        # Send response
        await message.answer(response_text)

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await message.answer(
            "Sorry, I encountered an error. Please try again or /reset."
        )


async def main():
    """Start the bot"""
    global conversation_manager

    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "conversations").mkdir(exist_ok=True)

    # Initialize conversation manager
    conversation_manager = ConversationManager(DATA_DIR / "conversations")

    # Initialize bot
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Register handlers
    dp.message.register(handle_message, F.text)

    # Start polling
    logger.info("Bot started")
    try:
        await dp.start_polling(bot)
    finally:
        # Cleanup
        for client in claude_clients.values():
            await client.__aexit__(None, None, None)


if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Conversation Manager (`modules/conversation_manager.py`)

```python
"""Manage conversation history using JSON files"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class ConversationManager:
    """Manages per-user conversation history"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, user_id: int) -> Path:
        """Get path to user's conversation file"""
        return self.data_dir / f"{user_id}.json"

    def get_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Get conversation history for a user.

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        file_path = self._get_file_path(user_id)

        if not file_path.exists():
            return []

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Return last N messages
        messages = data.get("messages", [])
        return messages[-limit:]

    def add_message(self, user_id: int, role: str, content: str):
        """Add a message to user's history"""
        file_path = self._get_file_path(user_id)

        # Load existing data
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = {"user_id": user_id, "messages": []}

        # Add new message
        data["messages"].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Save
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def clear_history(self, user_id: int):
        """Clear conversation history for a user"""
        file_path = self._get_file_path(user_id)

        if file_path.exists():
            file_path.unlink()

    def get_all_users(self) -> List[int]:
        """Get list of all user IDs with conversations"""
        return [
            int(f.stem)
            for f in self.data_dir.glob("*.json")
            if f.stem.isdigit()
        ]
```

### 3. System Prompt (`prompts/system_prompt.md`)

```markdown
You are a helpful AI assistant for [specific purpose].

## Your Role

[Define the agent's specific purpose and capabilities]

## Guidelines

- Be concise and helpful
- [Add specific behavioral guidelines]
- [Add constraints or boundaries]

## Example Interactions

User: [example question]
Assistant: [example response]
```

### 4. Configuration (`.env.example`)

```bash
# Telegram Bot Token (from @BotFather)
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Claude API Key
ANTHROPIC_API_KEY=sk-ant-...

# Claude Model
CLAUDE_MODEL=claude-sonnet-4-5-20241022

# Optional: Enable debug logging
DEBUG=false
```

### 5. Dependencies (`requirements.txt`)

```txt
aiogram==3.13.1
claude-agent-sdk==0.3.0
python-dotenv==1.0.0
```

### 6. Gitignore (`.gitignore`)

```gitignore
# Environment
.env

# Virtual environment
.venv/
venv/

# User data
data/

# Python
__pycache__/
*.pyc
*.pyo

# IDE
.vscode/
.idea/
```

## Advanced Patterns

### Audio Transcription Support

```python
# modules/transcribe.py
import os
from pathlib import Path
import httpx


async def transcribe_audio(audio_file_path: Path) -> str:
    """
    Transcribe audio using Claude or external service.

    Args:
        audio_file_path: Path to audio file

    Returns:
        Transcribed text
    """
    # Example using an external API
    api_key = os.getenv("TRANSCRIPTION_API_KEY")

    async with httpx.AsyncClient() as client:
        with open(audio_file_path, "rb") as f:
            response = await client.post(
                "https://api.transcription-service.com/v1/transcribe",
                files={"file": f},
                headers={"Authorization": f"Bearer {api_key}"},
            )

        result = response.json()
        return result["text"]


# In bot.py, add voice message handler:
@dp.message.register(F.voice)
async def handle_voice(message: Message):
    """Handle voice message"""
    # Download voice file
    file = await message.bot.get_file(message.voice.file_id)
    file_path = DATA_DIR / f"voice_{message.from_user.id}.ogg"

    await message.bot.download_file(file.file_path, file_path)

    # Transcribe
    text = await transcribe_audio(file_path)

    # Process as text message
    message.text = text
    await handle_message(message)

    # Cleanup
    file_path.unlink()
```

### User Preferences

```python
# modules/user_prefs.py
import json
from pathlib import Path


class UserPreferences:
    """Manage user preferences"""

    def __init__(self, prefs_file: Path):
        self.prefs_file = prefs_file
        self._load()

    def _load(self):
        if self.prefs_file.exists():
            with open(self.prefs_file, 'r') as f:
                self.prefs = json.load(f)
        else:
            self.prefs = {}

    def _save(self):
        with open(self.prefs_file, 'w') as f:
            json.dump(self.prefs, f, indent=2)

    def get(self, user_id: int, key: str, default=None):
        """Get user preference"""
        user_prefs = self.prefs.get(str(user_id), {})
        return user_prefs.get(key, default)

    def set(self, user_id: int, key: str, value):
        """Set user preference"""
        user_id_str = str(user_id)
        if user_id_str not in self.prefs:
            self.prefs[user_id_str] = {}

        self.prefs[user_id_str][key] = value
        self._save()
```

### Custom Tools for Telegram Bot

```python
# In bot.py, add custom tools:
from claude_agent_sdk import tool


@tool
async def get_user_preference(user_id: int, key: str) -> str:
    """
    Get a user preference value.

    Args:
        user_id: Telegram user ID
        key: Preference key

    Returns:
        Preference value or "not set"
    """
    prefs = UserPreferences(DATA_DIR / "user_prefs.json")
    value = prefs.get(user_id, key)
    return value if value else "not set"


# Register tools with client:
options = ClaudeAgentOptions(
    cwd=str(PROJECT_ROOT),
    system_prompt=system_prompt,
    model=CLAUDE_MODEL,
    permission_mode="bypassPermissions",
    max_turns=5,
    custom_tools=[get_user_preference],  # Register custom tools
)
```

## Deployment

### Local Development

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your tokens

# Run
python bot.py
```

### Production (Systemd Service)

```ini
# /etc/systemd/system/telegram-bot.service
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/telegram_bot
Environment="PATH=/opt/telegram_bot/.venv/bin"
ExecStart=/opt/telegram_bot/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# View logs
sudo journalctl -u telegram-bot -f
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory
RUN mkdir -p data/conversations

CMD ["python", "bot.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  bot:
    build: .
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data
```

```bash
# Run
docker-compose up -d

# View logs
docker-compose logs -f
```

## Key Patterns

### Per-User Isolation

Each user gets their own:
- Claude SDK client (maintains conversation context)
- Conversation history file
- Preferences

This ensures complete isolation between users.

### Stateless vs Stateful

**Stateless** (recommended for simple bots):
- No conversation history
- Each message is independent
- Lower storage requirements

**Stateful** (this pattern):
- Maintains conversation history
- Context-aware responses
- Better for complex interactions

### Error Handling

```python
try:
    response = await client.query(user_text, history=history)
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)

    # User-friendly error message
    if "rate_limit" in str(e).lower():
        await message.answer("I'm a bit busy. Please try again in a moment.")
    elif "timeout" in str(e).lower():
        await message.answer("Request timed out. Please try again.")
    else:
        await message.answer("Something went wrong. Please /reset and try again.")
```

## Summary

This pattern is ideal for:
- Single-purpose bots
- Personal or small-group use
- No web interface needed
- Simple data requirements
- Quick prototyping
- Low infrastructure overhead
