# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an AI assistant that integrates with macOS Calendar.app and Mail.app to help users manage tasks, events, and emails through natural language. The assistant provides both a command-line interface and a web-based interface.

## Directory Structure

```
ai_assistant/
├── src/
│   ├── cli.py                    # Core assistant logic with stepwise execution orchestrator and interactive chat interface
│   ├── web_server.py             # Flask-based web interface with Socket.IO for real-time communication
│   ├── launcher.py               # Simple launcher script that starts the web server and opens browser
│   ├── integrations/
│   │   ├── calendar_client.py    # macOS Calendar.app integration via AppleScript with configuration support
│   │   └── mail_client.py        # macOS Mail.app integration via AppleScript
│   ├── core/
│   │   ├── context.py            # Provides temporal and system context (date, time, timezone, platform info)
│   │   └── logging.py            # Centralized logging configuration
│   └── web/
│       └── templates/
│           └── index.html        # Web UI template
├── tests/
│   ├── test_calendar_integration.py  # Calendar.app functionality tests
│   ├── test_mail_integration.py      # Mail.app functionality tests
│   ├── test_mail_sending.py          # Email sending tests
│   └── test_search_functionality.py  # Search and aggregation tests
├── config/
│   └── calendar_config.json      # Calendar integration configuration
├── README.md
├── CLAUDE.md
└── requirements.txt
```

## Architecture

The codebase follows a modular architecture with clear separation of concerns across organized directories:

### Key Design Patterns

- **Tool-based Architecture**: Uses a unified Tools class that dispatches to Calendar and Mail tool implementations
- **Stepwise Execution**: AI assistant plans and executes one action at a time, observing results before next step
- **AppleScript Integration**: Native macOS integration through subprocess calls to osascript
- **Configuration-driven**: Calendar integration uses JSON config file for enabled/disabled calendars
- **Dual Interface**: Both CLI (`main.py`) and web UI (`web_ui.py`) share the same core logic

## Commands

### Development and Testing

```bash
# Run CLI interface
python src/cli.py

# Run web interface  
python src/web_server.py
# OR use the launcher
python src/launcher.py

# Run individual component tests
python tests/test_calendar_integration.py
python tests/test_mail_integration.py
python tests/test_search_functionality.py
python tests/test_mail_sending.py
```

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set required environment variable
export ANTHROPIC_API_KEY="your-api-key-here"

# Optional environment variables
export LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
export DEBUG_MODE=true         # Enable debug logging
```

## Key Components

### Tool System
- Tools are registered in a catalog with uniform interface
- Calendar tools: list, calendars, search, create, delete
- Mail tools: accounts, mailboxes, search, get, send, reply
- Tool calls return structured data with success/error status

### Web Interface
- Real-time chat using Flask-SocketIO
- Status indicators for Calendar.app and Mail.app availability
- Responsive design with typing indicators and action summaries
- Templates are auto-generated in code (see `create_templates_dir()`)

### Configuration
- `config/calendar_config.json` controls which calendars are enabled/disabled
- Default config disables Holiday, Birthday, and Siri Suggestions calendars
- Timeout and pattern-based filtering supported

### AppleScript Integration
- All macOS app interactions use AppleScript via subprocess
- Proper timeout handling and error capture
- Debug logging shows full AppleScript commands when LOG_LEVEL=DEBUG

## Important Notes

- This assistant requires macOS and uses AppleScript for Calendar.app and Mail.app integration
- The web interface runs on port 8080 by default
- Logs are written to both console and `ai_assistant.log` file
- The API key is hardcoded in src/cli.py:292 and should be moved to environment variable
- Templates directory is created programmatically if missing