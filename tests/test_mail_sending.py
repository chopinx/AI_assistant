#!/usr/bin/env python3
"""
Test Mail.app sending functionality
"""

from ai_assistant.integrations.mail_client import MacMailClient, MacMailTools
from ai_assistant.core.logging import get_logger

logger = get_logger('test_mail_send')

def test_send():
    """Test email sending"""
    mail_client = MacMailClient()
    mail_tools = MacMailTools(mail_client)
    
    print("📧 Testing Mail.app Send")
    print("-" * 30)
    
    # Show accounts
    accounts_result = mail_tools.call("mail.accounts", {})
    print(f"Available accounts: {accounts_result['data']['accounts']}")
    
    # Test sending to yourself (safer for testing)
    test_email = "xiaoqinbang@gmail.com"  # Replace with your email
    
    result = mail_tools.call("mail.send", {
        "to": test_email,
        "subject": "Test from AI Assistant",
        "content": "This is a test email from the AI assistant.\n\nIt has multiple lines\nand should work correctly now!",
        "account_name": "Google"  # Adjust if needed
    })
    
    print(f"Send result: {result}")

if __name__ == "__main__":
    test_send()