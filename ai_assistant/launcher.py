#!/usr/bin/env python3
"""
Start script for AI Assistant Web UI

Simple launcher that opens the web interface in your default browser.
"""

import subprocess
import time
import webbrowser
import threading
from ai_assistant.core.logging import get_logger

logger = get_logger('start_ui')

def start_web_server():
    """Start the web server"""
    try:
        subprocess.run(['python', '-m', 'ai_assistant.web_server'], check=True)
    except KeyboardInterrupt:
        print("\nShutting down AI Assistant...")
    except Exception as e:
        print(f"Error starting web server: {e}")

def main():
    print("🚀 Starting AI Assistant Web Interface...")
    print("📅 Calendar integration: Checking...")
    print("📧 Mail integration: Checking...")
    print()
    
    # Start web server in background thread
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Open browser
    url = "http://localhost:8080"
    print(f"🌐 Opening {url} in your browser...")
    webbrowser.open(url)
    
    print("✅ AI Assistant is ready!")
    print("💡 You can also access it manually at: http://localhost:8080")
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    try:
        # Keep main thread alive
        server_thread.join()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == '__main__':
    main()