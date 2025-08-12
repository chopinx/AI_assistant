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
from ai_assistant.cli import Tools, CALENDAR_APP_AVAILABLE, MAIL_APP_AVAILABLE
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
        """Process user message and return response with progress updates"""
        try:
            logger.info(f"Processing message from session {session_id}: {message}")
            
            # Create progress callback to emit real-time updates
            def progress_callback(event_type, data):
                emit('progress_update', {
                    'type': event_type,
                    'data': data
                }, room=session_id)
            
            # Run the assistant logic with progress tracking
            result = self._run_with_progress(message, progress_callback)
            
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
    
    def _run_with_progress(self, goal, progress_callback):
        """Enhanced run function with progress updates"""
        import os
        from anthropic import Anthropic
        from ai_assistant.cli import safe_json, llm, SYSTEM_ONE_STEP, SYSTEM_FINALIZER, Tools
        from ai_assistant.core.context import get_context_for_ai
        import json
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        
        client = Anthropic(api_key=api_key)
        tools = Tools()
        observations = []
        max_steps = 12
        
        progress_callback('thinking', {'message': 'Understanding your request...'})
        
        for step_num in range(max_steps):
            # Update progress for AI thinking
            progress_callback('thinking', {
                'message': f'Planning step {step_num + 1}...',
                'step': step_num + 1,
                'max_steps': max_steps
            })
            
            # Create view with minimal context
            context_info = get_context_for_ai()
            view = {"goal": goal, "tool_catalog": tools.catalog, "observations": observations}
            
            # Get step from AI
            system_prompt = SYSTEM_ONE_STEP.format(system_context=context_info)
            step = safe_json(llm(client, system_prompt, view))
            logger.debug(f"Step: {json.dumps(step, indent=2)}")

            # Handle direct finalize response
            if step.get("type") == "finalize":
                progress_callback('finalizing', {'message': 'Completing task...'})
                return {"summary": step["message"], "observations": observations}

            # Check if we should finalize
            if step.get("next", {}).get("type") == "finalize":
                progress_callback('finalizing', {'message': 'Generating final response...'})
                final = safe_json(llm(client, SYSTEM_FINALIZER, {"goal": goal, "observations": observations}))
                return {"summary": final["message"], "observations": observations}

            # Execute tool if needed
            if "next" in step and step["next"].get("name"):
                tool_name = step["next"]["name"]
                tool_args = step["next"].get("args", {})
                
                progress_callback('tool_execution', {
                    'message': f'Executing {tool_name}...',
                    'tool': tool_name,
                    'args': tool_args
                })
                
                # Execute the tool
                try:
                    result = tools.call(tool_name, tool_args)
                    observations.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "ok": True,
                        "data": result
                    })
                    
                    progress_callback('tool_completed', {
                        'message': f'Completed {tool_name}',
                        'tool': tool_name,
                        'success': True
                    })
                    
                except Exception as e:
                    observations.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "ok": False,
                        "error": str(e)
                    })
                    
                    progress_callback('tool_error', {
                        'message': f'Error in {tool_name}: {str(e)}',
                        'tool': tool_name,
                        'success': False,
                        'error': str(e)
                    })
            else:
                logger.warning(f"No 'next' key in step: {step}")
                progress_callback('error', {'message': 'AI response was incomplete'})
                return {"summary": "Invalid response from AI - missing action", "observations": observations}
        
        # If we reach here, we've hit max steps
        progress_callback('finalizing', {'message': 'Reached maximum steps, generating response...'})
        final = safe_json(llm(client, SYSTEM_FINALIZER, {"goal": goal, "observations": observations}))
        return {"summary": final["message"], "observations": observations}
    
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
    
    # Show typing indicator briefly
    emit('assistant_typing', {'typing': True})
    
    try:
        # Process the message (this will emit progress updates)
        response = assistant.process_message(message, session_id)
        
        # Send the response
        emit('assistant_typing', {'typing': False})
        emit('assistant_message', response)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        emit('assistant_typing', {'typing': False})
        emit('progress_update', {
            'type': 'error',
            'data': {'message': f'Error: {str(e)}'}
        })
        emit('assistant_message', {
            'success': False,
            'summary': 'Sorry, I encountered an error processing your message.',
            'actions': []
        })


if __name__ == '__main__':
    logger.info("Starting AI Assistant Web UI")
    logger.info("Calendar integration: " + ("✅" if CALENDAR_APP_AVAILABLE else "❌"))
    logger.info("Mail integration: " + ("✅" if MAIL_APP_AVAILABLE else "❌"))
    
    # Start the web server
    socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)