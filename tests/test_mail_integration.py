#!/usr/bin/env python3
"""
Test Mac Mail.app Integration

This script tests the Mac Mail.app client functionality.
"""

from src.integrations.mail_client import MacMailClient, MacMailTools
import json
from src.core.logging import get_logger

logger = get_logger('test_mail')

def test_mail():
    """Test Mail.app functionality"""
    print("🧪 Testing Mac Mail.app Integration")
    print("-" * 40)
    
    # Initialize client
    mail_client = MacMailClient()
    mail_tools = MacMailTools(mail_client)
    
    # Test accounts
    print("1. Testing accounts...")
    accounts_result = mail_tools.call("mail.accounts", {})
    print(f"   Result: {accounts_result}")
    
    if accounts_result["ok"]:
        accounts = accounts_result["data"]["accounts"]
        print(f"✅ Found {len(accounts)} accounts: {', '.join(accounts)}")
        
        if accounts:
            account = accounts[0]
            
            # Test mailboxes
            print(f"\n2. Testing mailboxes for {account}...")
            mailbox_result = mail_tools.call("mail.mailboxes", {"account_name": account})
            if mailbox_result["ok"]:
                mailboxes = mailbox_result["data"]["mailboxes"]
                print(f"   Found {len(mailboxes)} mailboxes: {', '.join(mailboxes)}")
            
            # Test search
            print(f"\n3. Testing message search in {account}/INBOX...")
            search_result = mail_tools.call("mail.search", {
                "account_name": account,
                "mailbox": "INBOX",
                "limit": 5
            })
            
            if search_result["ok"]:
                messages = search_result["data"]["messages"]
                print(f"   Found {len(messages)} messages")
                
                # Show first few messages
                for i, msg in enumerate(messages[:3], 1):
                    print(f"   {i}. {msg['subject'][:50]}... from {msg['sender'][:30]}")
                    print(f"      Date: {msg['date']}, Read: {msg['read']}")
                
                # Test getting message content
                if messages:
                    print(f"\n4. Testing get message content...")
                    first_msg = messages[0]
                    content_result = mail_tools.call("mail.get", {
                        "message_index": first_msg["index"],
                        "account_name": account,
                        "mailbox": "INBOX"
                    })
                    
                    if content_result["ok"]:
                        msg_data = content_result["data"]
                        print(f"   Subject: {msg_data['subject']}")
                        print(f"   From: {msg_data['sender']}")
                        print(f"   Content preview: {msg_data['content'][:100]}...")
            else:
                print(f"   Error: {search_result['data'].get('error', 'Unknown error')}")
    
    print("\n✅ Mac Mail.app integration test completed!")
    return True

def interactive_test():
    """Interactive test mode"""
    mail_client = MacMailClient()
    mail_tools = MacMailTools(mail_client)
    
    print("🔧 Interactive Mac Mail Test Mode")
    print("Available commands: accounts, mailboxes, search, get, send, reply, quit")
    
    while True:
        command = input("\nEnter command: ").strip().lower()
        
        if command == "quit":
            break
        elif command == "accounts":
            result = mail_tools.call("mail.accounts", {})
            print(json.dumps(result, indent=2))
        elif command == "mailboxes":
            account = input("Account name (or press Enter for default): ").strip()
            args = {"account_name": account} if account else {}
            result = mail_tools.call("mail.mailboxes", args)
            print(json.dumps(result, indent=2))
        elif command == "search":
            query = input("Search query (optional): ").strip()
            mailbox = input("Mailbox (default INBOX): ").strip() or "INBOX"
            account = input("Account (optional): ").strip()
            limit = input("Limit (default 10): ").strip()
            
            args = {
                "mailbox": mailbox,
                "limit": int(limit) if limit else 10
            }
            if query:
                args["query"] = query
            if account:
                args["account_name"] = account
                
            result = mail_tools.call("mail.search", args)
            print(json.dumps(result, indent=2))
        elif command == "get":
            index = int(input("Message index: "))
            mailbox = input("Mailbox (default INBOX): ").strip() or "INBOX"
            account = input("Account (optional): ").strip()
            
            args = {
                "message_index": index,
                "mailbox": mailbox
            }
            if account:
                args["account_name"] = account
                
            result = mail_tools.call("mail.get", args)
            print(json.dumps(result, indent=2))
        elif command == "send":
            to = input("To: ")
            subject = input("Subject: ")
            content = input("Content: ")
            account = input("Account (optional): ").strip()
            
            args = {
                "to": to,
                "subject": subject,
                "content": content
            }
            if account:
                args["account_name"] = account
                
            result = mail_tools.call("mail.send", args)
            print(json.dumps(result, indent=2))
        elif command == "reply":
            index = int(input("Reply to message index: "))
            content = input("Reply content: ")
            mailbox = input("Mailbox (default INBOX): ").strip() or "INBOX"
            account = input("Account (optional): ").strip()
            
            args = {
                "message_index": index,
                "content": content,
                "mailbox": mailbox
            }
            if account:
                args["account_name"] = account
                
            result = mail_tools.call("mail.reply", args)
            print(json.dumps(result, indent=2))
        else:
            print("Unknown command. Available: accounts, mailboxes, search, get, send, reply, quit")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        test_mail()