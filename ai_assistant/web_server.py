#!/usr/bin/env python3
"""
Web UI for AI Assistant

A modern web interface for the AI assistant with real-time chat.
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import os
from ai_assistant.core.logging import get_logger

# Import the existing assistant logic
from ai_assistant.cli import run, Tools, CALENDAR_APP_AVAILABLE, MAIL_APP_AVAILABLE
from ai_assistant.cli import calendar_client, mail_client
from ai_assistant.core.context import get_context_for_ai

# Setup logging for web UI
logger = get_logger('web_ui')

app = Flask(__name__, template_folder='web/templates')
app.config['SECRET_KEY'] = 'ai_assistant_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

class WebAssistant:
    """Web interface wrapper for the AI assistant"""
    
    def __init__(self):
        self.tools = Tools()
        self.active_sessions = {}
    
    def get_status(self):
        """Get integration status"""
        status = {
            "calendar": {
                "available": CALENDAR_APP_AVAILABLE,
                "calendars": calendar_client.calendars[:5] if CALENDAR_APP_AVAILABLE else [],
                "total_calendars": len(calendar_client.calendars) if CALENDAR_APP_AVAILABLE else 0
            },
            "mail": {
                "available": MAIL_APP_AVAILABLE,
                "accounts": mail_client.accounts if MAIL_APP_AVAILABLE else [],
                "total_accounts": len(mail_client.accounts) if MAIL_APP_AVAILABLE else 0
            }
        }
        return status
    
    def process_message(self, message, session_id):
        """Process user message and return response"""
        try:
            logger.info(f"Processing message from session {session_id}: {message}")
            
            # Run the assistant logic
            result = run(message)
            
            response = {
                "success": True,
                "summary": result.get('summary', 'Task completed'),
                "actions": []
            }
            
            # Process observations into user-friendly actions
            if result.get('observations'):
                for obs in result['observations']:
                    if obs.get('ok'):
                        tool = obs['tool']
                        data = obs['data']
                        
                        action = {
                            "tool": tool,
                            "success": True,
                            "message": self._format_tool_result(tool, data)
                        }
                        response["actions"].append(action)
                    else:
                        action = {
                            "tool": obs['tool'],
                            "success": False,
                            "message": f"Error: {obs.get('error', 'Unknown error')}"
                        }
                        response["actions"].append(action)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "summary": f"Sorry, I encountered an error: {str(e)}",
                "actions": []
            }
    
    def _format_tool_result(self, tool, data):
        """Format tool results for display"""
        if tool == 'calendar.list':
            events = data.get('events', [])
            calendars_searched = data.get('calendars_searched', [])
            if calendars_searched:
                return f"Listed {len(events)} events from {len(calendars_searched)} calendars"
            else:
                return f"Listed {len(events)} calendar events"
        elif tool == 'calendar.calendars':
            calendars = data.get('calendars', [])
            return f"Found {len(calendars)} calendars"
        elif tool == 'calendar.search':
            count = data.get('count', 0)
            keyword = data.get('keyword', 'N/A')
            calendars_searched = data.get('calendars_searched', [])
            if calendars_searched:
                return f"Found {count} events matching '{keyword}' across {len(calendars_searched)} calendars"
            else:
                return f"Found {count} events matching '{keyword}'"
        elif tool == 'calendar.create':
            created = data.get('created', False)
            title = data.get('title', 'Unknown')
            return f"Calendar event {'created' if created else 'failed to create'}: '{title}'"
        elif tool == 'calendar.delete':
            deleted = data.get('deleted', False)
            title = data.get('title', 'Unknown')
            return f"Calendar event {'deleted' if deleted else 'failed to delete'}: '{title}'"
        elif tool == 'mail.accounts':
            accounts = data.get('accounts', [])
            return f"Found {len(accounts)} Mail accounts: {', '.join(accounts)}"
        elif tool == 'mail.search':
            count = data.get('count', 0)
            accounts_searched = data.get('accounts_searched', [])
            query = data.get('query', 'messages')
            if accounts_searched:
                return f"Found {count} {query} across {len(accounts_searched)} accounts"
            else:
                account = data.get('account', 'Unknown')
                mailbox = data.get('mailbox', 'Unknown')
                return f"Found {count} messages in {account}/{mailbox}"
        elif tool == 'mail.send':
            sent = data.get('sent', False)
            to = data.get('to', 'Unknown')
            return f"Mail {'sent successfully' if sent else 'failed to send'} to {to}"
        elif tool == 'mail.reply':
            reply_sent = data.get('reply_sent', False)
            return f"Mail reply {'sent successfully' if reply_sent else 'failed to send'}"
        else:
            return f"Executed {tool}"

# Global assistant instance
assistant = WebAssistant()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get system status"""
    return assistant.get_status()

@app.route('/api/context')
def api_context():
    """Get current system context"""
    try:
        context = get_context_for_ai()
        return {"context": context, "success": True}
    except Exception as e:
        logger.error(f"Error getting system context: {e}")
        return {"error": str(e), "success": False}

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    status = assistant.get_status()
    emit('status_update', status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('send_message')
def handle_message(data):
    """Handle incoming chat message"""
    message = data.get('message', '').strip()
    session_id = request.sid
    
    if not message:
        return
    
    logger.info(f"Received message from {session_id}: {message}")
    
    # Echo the user message
    emit('user_message', {'message': message})
    
    # Show typing indicator
    emit('assistant_typing', {'typing': True})
    
    try:
        # Process the message
        response = assistant.process_message(message, session_id)
        
        # Send the response
        emit('assistant_typing', {'typing': False})
        emit('assistant_message', response)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        emit('assistant_typing', {'typing': False})
        emit('assistant_message', {
            'success': False,
            'summary': 'Sorry, I encountered an error processing your message.',
            'actions': []
        })

def create_templates_dir():
    """Create templates directory and HTML file"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'web', 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Assistant</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            width: 90%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        
        .status {
            display: flex;
            justify-content: center;
            gap: 20px;
            font-size: 14px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #27ae60;
        }
        
        .status-indicator.disabled {
            background: #e74c3c;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        
        .user-message {
            align-self: flex-end;
            background: #007AFF;
            color: white;
        }
        
        .assistant-message {
            align-self: flex-start;
            background: #f1f1f1;
            color: #333;
        }
        
        .assistant-message.error {
            background: #ffebee;
            color: #c62828;
        }
        
        .actions {
            margin-top: 10px;
            font-size: 14px;
        }
        
        .action-item {
            margin: 5px 0;
            padding: 8px 12px;
            background: #e8f5e8;
            border-radius: 8px;
            border-left: 3px solid #4caf50;
        }
        
        .action-item.error {
            background: #ffebee;
            border-left-color: #f44336;
        }
        
        .typing-indicator {
            align-self: flex-start;
            background: #f1f1f1;
            color: #666;
            font-style: italic;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 0.7; }
            50% { opacity: 1; }
        }
        
        .input-container {
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #e9ecef;
        }
        
        .input-form {
            display: flex;
            gap: 10px;
        }
        
        .message-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .message-input:focus {
            border-color: #007AFF;
        }
        
        .send-button {
            padding: 12px 24px;
            background: #007AFF;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        
        .send-button:hover {
            background: #0056b3;
        }
        
        .send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Assistant</h1>
            <div class="status" id="status">
                <div class="status-item">
                    <div class="status-indicator disabled" id="calendar-status"></div>
                    <span>Calendar</span>
                </div>
                <div class="status-item">
                    <div class="status-indicator disabled" id="mail-status"></div>
                    <span>Email</span>
                </div>
            </div>
        </div>
        
        <div class="chat-container" id="chat">
            <div class="message assistant-message">
                👋 Hi! I'm your AI assistant. I can help you manage your calendar events and emails. Try asking me something like:
                <ul style="margin-top: 10px; padding-left: 20px;">
                    <li>"Show my events for next week"</li>
                    <li>"Send an email to john@example.com"</li>
                    <li>"Create a meeting tomorrow at 2pm"</li>
                </ul>
            </div>
        </div>
        
        <div class="input-container">
            <form class="input-form" id="messageForm">
                <input type="text" class="message-input" id="messageInput" 
                       placeholder="Type your message..." autocomplete="off">
                <button type="submit" class="send-button" id="sendButton">Send</button>
            </form>
        </div>
    </div>

    <script>
        const socket = io();
        const chat = document.getElementById('chat');
        const messageForm = document.getElementById('messageForm');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        let typingIndicator = null;
        
        // Auto-scroll to bottom
        function scrollToBottom() {
            chat.scrollTop = chat.scrollHeight;
        }
        
        // Add message to chat
        function addMessage(content, className) {
            const message = document.createElement('div');
            message.className = `message ${className}`;
            message.innerHTML = content;
            chat.appendChild(message);
            scrollToBottom();
            return message;
        }
        
        // Show/hide typing indicator
        function showTyping(show) {
            if (show && !typingIndicator) {
                typingIndicator = addMessage('Assistant is typing...', 'typing-indicator');
            } else if (!show && typingIndicator) {
                typingIndicator.remove();
                typingIndicator = null;
            }
        }
        
        // Update status indicators
        function updateStatus(status) {
            const calendarStatus = document.getElementById('calendar-status');
            const mailStatus = document.getElementById('mail-status');
            
            calendarStatus.className = status.calendar.available ? 
                'status-indicator' : 'status-indicator disabled';
            mailStatus.className = status.mail.available ? 
                'status-indicator' : 'status-indicator disabled';
        }
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to server');
        });
        
        socket.on('status_update', function(status) {
            updateStatus(status);
        });
        
        socket.on('user_message', function(data) {
            addMessage(data.message, 'user-message');
        });
        
        socket.on('assistant_typing', function(data) {
            showTyping(data.typing);
        });
        
        socket.on('assistant_message', function(data) {
            let content = data.summary;
            
            if (data.actions && data.actions.length > 0) {
                content += '<div class="actions">';
                data.actions.forEach(action => {
                    const actionClass = action.success ? 'action-item' : 'action-item error';
                    content += `<div class="${actionClass}">• ${action.message}</div>`;
                });
                content += '</div>';
            }
            
            const className = data.success ? 'assistant-message' : 'assistant-message error';
            addMessage(content, className);
        });
        
        // Form submission
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            
            if (message) {
                socket.emit('send_message', { message: message });
                messageInput.value = '';
                sendButton.disabled = true;
                setTimeout(() => { sendButton.disabled = false; }, 1000);
            }
        });
        
        // Auto-focus input
        messageInput.focus();
    </script>
</body>
</html>
    '''
    
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    # Create templates directory
    create_templates_dir()
    
    logger.info("Starting AI Assistant Web UI")
    logger.info("Calendar integration: " + ("✅" if CALENDAR_APP_AVAILABLE else "❌"))
    logger.info("Mail integration: " + ("✅" if MAIL_APP_AVAILABLE else "❌"))
    
    # Start the web server
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)