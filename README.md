# AI Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)

An AI assistant that integrates with macOS Calendar.app and Mail.app to help you manage tasks, events, and emails through natural language. Provides both a command-line interface and a web-based interface.

## 🚀 Features

- **📅 Calendar Integration** - Manage events in your Mac Calendar.app
- **📧 Email Integration** - Send, read, and reply to emails via Mac Mail.app  
- **💬 Natural Language** - Chat with the AI in plain English
- **⚡ Real-time Sync** - Changes reflect immediately in native Mac apps
- **🖥️ Dual Interface** - Command-line and web-based interfaces
- **⚙️ Configuration** - Customizable calendar filtering
- **🔒 Secure** - Environment variable API key management
- **📊 Logging** - Comprehensive logging with configurable levels

## 📋 Requirements

- **macOS** (tested on macOS 14+)
- **Python 3.11+**
- **Calendar.app** and **Mail.app** (built-in macOS apps)
- **Anthropic API key** ([get one here](https://console.anthropic.com/))

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chopinx/AI_assistant.git
   cd AI_assistant
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set your Anthropic API key:**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
   
   Or add to your shell profile:
   ```bash
   echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
   source ~/.zshrc
   ```

## 🚀 Usage

### Command-line Interface
```bash
python -m ai_assistant.cli
```

### Web Interface
```bash
python -m ai_assistant.web_server
```
Then open http://localhost:8080 in your browser

### Quick Launcher
```bash
python -m ai_assistant.launcher  # Starts web server and opens browser
```

## 💡 Examples

The assistant can help with:

### 📅 Calendar Management
- "Show my events for next week"
- "Create a meeting tomorrow at 2pm"
- "Search for doctor appointments"
- "Delete the event called 'Old Meeting'"
- "List all events in my Work calendar"

### 📧 Email Management
- "Check my recent emails"
- "Send an email to john@example.com about the project"
- "Reply to message 3 with thanks"
- "Search for emails from my boss"
- "Show emails in my Inbox from last week"

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | - | Your Anthropic API key |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `DEBUG_MODE` | ❌ | `false` | Enable debug logging for API calls |

### Calendar Configuration

Edit `config/calendar_config.json` to control which calendars are enabled:

```json
{
  "calendar_settings": {
    "enabled_calendars": {},
    "disabled_calendars": ["Holiday", "Birthday", "Siri Suggestions"],
    "default_enabled": true,
    "timeout_seconds": 15,
    "skip_patterns": ["Holiday", "Birthday", "Siri"]
  }
}
```

### Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Enable debug mode (shows all AppleScript calls)
export DEBUG_MODE=true
```

Logs are written to both console and `ai_assistant.log` file.

## 🏗️ Architecture

```
ai_assistant/
├── ai_assistant/
│   ├── cli.py                    # Command-line interface with stepwise execution
│   ├── web_server.py             # Flask web interface with Socket.IO
│   ├── launcher.py               # Web server launcher script
│   ├── integrations/
│   │   ├── calendar_client.py    # macOS Calendar.app integration via AppleScript
│   │   └── mail_client.py        # macOS Mail.app integration via AppleScript
│   ├── core/
│   │   ├── context.py            # Temporal and system context provider
│   │   └── logging.py            # Centralized logging configuration
│   └── web/
│       └── templates/
│           └── index.html        # Web UI template (auto-generated)
├── tests/                        # Comprehensive test suite
├── config/
│   └── calendar_config.json      # Calendar integration configuration
├── LICENSE                       # MIT License
├── README.md                     # This file
└── requirements.txt              # Python dependencies
```

## 🧪 Testing

Run the test suite:

```bash
# Run individual component tests
python tests/test_calendar_integration.py
python tests/test_mail_integration.py
python tests/test_search_functionality.py
python tests/test_mail_sending.py

# Run all tests
find tests/ -name "test_*.py" -exec python {} \;
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Issues & Support

- **Bug Reports**: [Create an issue](https://github.com/chopinx/AI_assistant/issues/new?template=bug_report.md)
- **Feature Requests**: [Create an issue](https://github.com/chopinx/AI_assistant/issues/new?template=feature_request.md)
- **Questions**: [Start a discussion](https://github.com/chopinx/AI_assistant/discussions)

## 🙏 Acknowledgments

- Built with [Anthropic's Claude API](https://www.anthropic.com/)
- Uses [Flask](https://flask.palletsprojects.com/) for the web interface
- Integrates with macOS native apps via AppleScript