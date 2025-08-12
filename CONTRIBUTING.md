# Contributing to AI Assistant

Thank you for your interest in contributing to AI Assistant! We welcome contributions from the community and are grateful for your help in making this project better.

## 🤝 How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with the following information:

1. **Bug Description**: A clear and concise description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: 
   - macOS version
   - Python version
   - AI Assistant version

### Suggesting Features

We love feature suggestions! Please create an issue with:

1. **Feature Description**: Clear description of the proposed feature
2. **Use Case**: Why this feature would be useful
3. **Implementation Ideas**: Any thoughts on how it could be implemented

### Submitting Code Changes

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/AI_assistant.git
   cd AI_assistant
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   export ANTHROPIC_API_KEY="your-api-key"
   ```

4. **Make Your Changes**
   - Write clean, readable code
   - Follow existing code style and conventions
   - Add tests for new functionality
   - Update documentation as needed

5. **Test Your Changes**
   ```bash
   # Run existing tests
   python tests/test_calendar_integration.py
   python tests/test_mail_integration.py
   python tests/test_search_functionality.py
   python tests/test_mail_sending.py
   
   # Test your specific changes
   python -m src.cli  # Test CLI interface
   python -m src.web_server  # Test web interface
   ```

6. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add: Clear description of your changes"
   ```

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

## 📝 Code Style Guidelines

### Python Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and reasonably sized
- Use type hints where appropriate

### Example Code Style

```python
def list_events(
    self,
    calendar_name: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """List events from Calendar.app
    
    Args:
        calendar_name: Optional calendar name to filter
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        limit: Maximum number of events to return
        
    Returns:
        Dictionary containing events and metadata
    """
    # Implementation here
```

### Commit Message Guidelines

Use clear, descriptive commit messages:

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

Examples:
```
feat: Add email attachment support
fix: Resolve calendar infinite loop issue
docs: Update installation instructions
test: Add calendar integration tests
```

## 🧪 Testing Guidelines

### Test Categories

1. **Integration Tests**: Test Calendar.app and Mail.app integration
2. **Unit Tests**: Test individual functions and classes
3. **End-to-End Tests**: Test complete user workflows

### Writing Tests

- Test both success and failure cases
- Use descriptive test names
- Include setup and teardown as needed
- Mock external dependencies when appropriate

### Test Structure

```python
def test_calendar_list_events_success():
    """Test successful event listing from calendar"""
    # Arrange
    client = MacCalendarClient()
    
    # Act
    result = client.list_events(limit=5)
    
    # Assert
    assert "events" in result
    assert isinstance(result["events"], list)
    assert len(result["events"]) <= 5
```

## 🔧 Development Setup

### Prerequisites

- macOS (for Calendar.app and Mail.app integration)
- Python 3.11+
- Anthropic API key

### Local Development

1. **Clone and setup**
   ```bash
   git clone https://github.com/chopinx/AI_assistant.git
   cd AI_assistant
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment variables**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   export LOG_LEVEL=DEBUG
   export DEBUG_MODE=true
   ```

3. **Run in development mode**
   ```bash
   # CLI interface
   python -m src.cli
   
   # Web interface with auto-reload
   python -m src.web_server
   ```

### AppleScript Testing

When working with AppleScript integration:

1. **Test manually first** - Verify AppleScript commands work in Script Editor
2. **Check permissions** - Ensure Calendar.app and Mail.app have proper permissions
3. **Handle timeouts** - AppleScript can be slow, test with realistic timeouts
4. **Test edge cases** - Empty calendars, missing data, etc.

## 📋 Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New functionality includes tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No sensitive information (API keys, etc.) is committed
- [ ] Changes are backward compatible (or breaking changes are documented)

## 🚫 What Not to Include

- API keys or other sensitive information
- Large binary files
- Generated files (unless necessary)
- OS-specific files (.DS_Store, Thumbs.db)
- IDE configuration files (unless project-wide standards)

## 🤔 Questions?

If you have questions about contributing:

- Check existing [issues](https://github.com/chopinx/AI_assistant/issues) and [discussions](https://github.com/chopinx/AI_assistant/discussions)
- Create a new discussion for general questions
- Create an issue for specific problems or bugs

## 📄 License

By contributing to AI Assistant, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Project documentation

Thank you for helping make AI Assistant better! 🎉