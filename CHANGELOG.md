# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial open source project structure
- GitHub issue templates and workflows
- Proper Python package configuration
- Code of conduct and security policy

## [0.1.0] - 2025-01-XX

### Added
- 🚀 **Core Features**
  - AI assistant with natural language interface
  - macOS Calendar.app integration via AppleScript
  - macOS Mail.app integration via AppleScript
  - Command-line interface (CLI)
  - Web-based interface with real-time updates
  - Configuration management for calendar filtering

- 📅 **Calendar Integration**
  - List events from Calendar.app
  - Create new calendar events
  - Search through calendar events
  - Delete calendar events
  - Support for multiple calendars
  - Configurable calendar filtering

- 📧 **Email Integration**
  - Read emails from Mail.app
  - Send new emails
  - Reply to existing emails
  - Search through mailboxes
  - Support for multiple email accounts

- 🖥️ **Interfaces**
  - Interactive command-line interface
  - Web UI with Socket.IO for real-time communication
  - Quick launcher script for web interface

- ⚙️ **Configuration & Management**
  - Environment variable configuration
  - JSON-based calendar settings
  - Comprehensive logging system
  - Debug mode support

- 🧪 **Testing & Quality**
  - Integration tests for Calendar.app
  - Integration tests for Mail.app
  - Search functionality tests
  - Email sending tests

### Technical Details
- **Platform**: macOS only (requires Calendar.app and Mail.app)
- **Python**: 3.11+ required
- **Architecture**: Modular design with tool-based system
- **Integration**: Native AppleScript integration
- **API**: Anthropic Claude API for AI functionality

### Dependencies
- anthropic>=0.62.0 (AI functionality)
- flask>=3.1.0 (Web interface)
- flask-socketio>=5.5.0 (Real-time communication)
- click>=8.2.0 (CLI interface)

[Unreleased]: https://github.com/chopinx/AI_assistant/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/chopinx/AI_assistant/releases/tag/v0.1.0