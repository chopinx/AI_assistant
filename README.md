# AI Assistant

An AI assistant that integrates with macOS Calendar.app and Mail.app to help you manage tasks, events, and emails through natural language. Provides both a command-line interface and a web-based interface.

## Features

- **Calendar Integration** - Manage events in your Mac Calendar.app
- **Email Integration** - Send, read, and reply to emails via Mac Mail.app  
- **Natural Language** - Chat with the AI in plain English
- **Real-time Sync** - Changes reflect immediately in native Mac apps
- **Dual Interface** - Command-line and web-based interfaces
- **Configuration** - Customizable calendar filtering

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

3. Run the assistant:
   
   **Command-line interface:**
   ```bash
   python -m src.cli
   ```
   
   **Web interface:**
   ```bash
   python -m src.web_server
   ```
   Then open http://localhost:8080 in your browser

## Usage

The assistant can help with:

### Calendar
- "Show my events for next week"
- "Create a meeting tomorrow at 2pm"
- "Search for doctor appointments"
- "Delete the event called 'Old Meeting'"

### Email
- "Check my recent emails"
- "Send an email to john@example.com about the project"
- "Reply to message 3 with thanks"
- "Search for emails from my boss"

## Logging

Control logging level with environment variables:

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR)
export LOG_LEVEL=INFO

# Enable debug mode (shows all API calls)
export DEBUG_MODE=true

# Then run either interface
python -m src.cli        # CLI interface
python -m src.web_server # Web interface
```

Logs are written to both console and `ai_assistant.log` file.

## Architecture

```
ai_assistant/
├── src/
│   ├── cli.py                    # Command-line interface
│   ├── web_server.py             # Web interface with Socket.IO
│   ├── launcher.py               # Web server launcher
│   ├── integrations/
│   │   ├── calendar_client.py    # macOS Calendar.app integration
│   │   └── mail_client.py        # macOS Mail.app integration
│   ├── core/
│   │   ├── context.py            # System context (date, time, etc.)
│   │   └── logging.py            # Centralized logging
│   └── web/
│       └── templates/
│           └── index.html        # Web UI template
├── tests/                        # Test scripts
├── config/
│   └── calendar_config.json      # Calendar configuration
└── requirements.txt
```

## Environment Variables

- `ANTHROPIC_API_KEY` - Required: Your Anthropic API key
- `LOG_LEVEL` - Optional: Logging level (default: INFO)
- `DEBUG_MODE` - Optional: Enable debug logging (default: false)