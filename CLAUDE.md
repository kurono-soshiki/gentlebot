# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gentlebot is a Discord bot with two main modules:
- **Yomiage (読み上げ)**: Text-to-speech functionality using VOICEVOX engine
- **Umigame (うみがめ)**: "Sea Turtle Soup" lateral thinking puzzle game using Google Gemini AI

## Essential Commands

### Development & Testing
```bash
# Install dependencies
uv sync

# Run the bot
uv run python src/main.py

# Run all tests
uv run pytest
uv run python src/test_runner.py

# Run specific test module
uv run pytest src/yomiage/
uv run pytest src/umigame/

# Run with coverage
uv run pytest --cov=src
```

### Docker Operations
```bash
# Start all services (bot + VOICEVOX)
sudo docker compose up -d --build

# View logs
sudo docker compose logs bot
sudo docker compose logs voicebox

# Stop services
sudo docker compose down
```

### Environment Setup
Required environment variables in `.env`:
```
DISCORD_TOKEN=your_discord_token
GEMINI_API_KEY=your_gemini_api_key
```

## Architecture Overview

### Module Structure
- `src/main.py`: Entry point that initializes Discord client and registers modules
- `src/config.py`: Environment variable management
- `src/yomiage/`: Text-to-speech module
  - `yomiage.py`: Discord commands, queue management, and `preprocess_text()` for text preprocessing
  - `voicebox.py`: VOICEVOX API integration (async, using aiohttp)
  - `database.py`: SQLite persistence using aiosqlite (server read_channel, user voice preferences)
  - `voice.json`: Voice configuration data
- `src/umigame/`: Puzzle game module using Gemini AI

### Key Patterns
1. **Async/Await**: All Discord operations use asyncio
2. **Queue Management**: Audio queue with `asyncio.Event` for message ordering
3. **Command Registration**: Uses `discord.app_commands.CommandTree`
4. **SQLite Persistence**: Settings (server read_channel, user voice preferences) are persisted to SQLite via aiosqlite

### External Services
- **VOICEVOX**: Runs as Docker container on port 50021
- **Google Gemini**: API for puzzle generation

### Dependencies
- **discord.py**: Discord bot framework
- **aiohttp**: Async HTTP client for VOICEVOX API
- **aiosqlite**: Async SQLite driver for settings persistence
- **google-genai**: Google Gemini AI integration

### Testing Approach
- Mock external services with `unittest.mock`
- Skip tests when API keys unavailable
- Async test support with event loops
- Test files pattern: `*_test.py`

## Important Notes

1. **No linting tools configured** - Consider adding flake8, black, or ruff
2. **Auto-disconnect**: Bot leaves VC when all users leave
3. **Text preprocessing**: Automatic URL shortening, character limits, special character removal (extracted as `preprocess_text()`)
4. **Per-user/per-server settings**: Voice preferences persisted to SQLite database
