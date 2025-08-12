#!/usr/bin/env python3
"""
Test Consolidated Search Functionality

Tests the new "search all" and "list all" functionality that aggregates results
from multiple calendars and email accounts.
"""

from src.integrations.calendar_client import MacCalendarClient, MacCalendarTools
from src.integrations.mail_client import MacMailClient, MacMailTools
import json
from src.core.logging import get_logger

logger = get_logger('test_consolidated')

def test_calendar_consolidated():
    """Test consolidated calendar search"""
    print("📅 Testing Calendar Consolidated Search")
    print("-" * 40)
    
    calendar_client = MacCalendarClient()
    calendar_tools = MacCalendarTools(calendar_client)
    
    print(f"Available calendars: {len(calendar_client.calendars)}")
    print(f"Calendars: {', '.join(calendar_client.calendars[:5])}...")
    print()
    
    # Test list all calendars (no calendar_name specified)
    print("1. Testing list all calendars...")
    result = calendar_tools.call("calendar.list", {"limit": 10})
    
    if result["ok"]:
        data = result["data"]
        events = data.get("events", [])
        calendars_searched = data.get("calendars_searched", [])
        
        print(f"✅ Found {len(events)} events across {len(calendars_searched)} calendars")
        print(f"   Calendars searched: {', '.join(calendars_searched[:3])}...")
        
        # Show some events
        for i, event in enumerate(events[:3], 1):
            print(f"   {i}. {event['title']} ({event['calendar']})")
    else:
        print(f"❌ Error: {result.get('data', {}).get('error', 'Unknown')}")
    
    print()
    
    # Test search all calendars
    print("2. Testing search across all calendars...")
    result = calendar_tools.call("calendar.search", {"keyword": "会议"})  # Chinese for meeting
    
    if result["ok"]:
        data = result["data"]
        events = data.get("events", [])
        calendars_searched = data.get("calendars_searched", [])
        
        print(f"✅ Found {len(events)} matching events across {len(calendars_searched)} calendars")
        
        for event in events[:2]:
            print(f"   - {event['title']} in {event['calendar']}")
    else:
        print(f"❌ Error: {result.get('data', {}).get('error', 'Unknown')}")
    
    print()

def test_mail_consolidated():
    """Test consolidated mail search"""
    print("📧 Testing Mail Consolidated Search")
    print("-" * 40)
    
    mail_client = MacMailClient()
    mail_tools = MacMailTools(mail_client)
    
    print(f"Available accounts: {len(mail_client.accounts)}")
    print(f"Accounts: {', '.join(mail_client.accounts)}")
    print()
    
    # Test search all accounts (no account_name specified)
    print("1. Testing search all accounts...")
    result = mail_tools.call("mail.search", {"limit": 5})
    
    if result["ok"]:
        data = result["data"]
        messages = data.get("messages", [])
        accounts_searched = data.get("accounts_searched", [])
        
        print(f"✅ Found {len(messages)} messages across {len(accounts_searched)} accounts")
        print(f"   Accounts searched: {', '.join(accounts_searched)}")
        
        # Show some messages
        for i, msg in enumerate(messages[:3], 1):
            print(f"   {i}. {msg['subject'][:40]}... ({msg['account']})")
    else:
        print(f"❌ Error: {result.get('data', {}).get('error', 'Unknown')}")
    
    print()
    
    # Test search with query across all accounts
    print("2. Testing search with query across all accounts...")
    result = mail_tools.call("mail.search", {"query": "project", "limit": 3})
    
    if result["ok"]:
        data = result["data"]
        messages = data.get("messages", [])
        accounts_searched = data.get("accounts_searched", [])
        
        print(f"✅ Found {len(messages)} messages matching 'project' across {len(accounts_searched)} accounts")
        
        for msg in messages:
            print(f"   - {msg['subject'][:50]}... from {msg['sender'][:20]} ({msg['account']})")
    else:
        print(f"❌ Error: {result.get('data', {}).get('error', 'Unknown')}")
    
    print()

def main():
    """Run consolidated search tests"""
    print("🧪 Testing Consolidated Search Functionality")
    print("=" * 50)
    print()
    
    try:
        test_calendar_consolidated()
        test_mail_consolidated()
        
        print("✅ Consolidated search testing completed!")
        print()
        print("📋 Summary:")
        print("- Calendar tools now search all calendars when none specified")
        print("- Mail tools now search all accounts when none specified")
        print("- Results are aggregated internally within each tool")
        print("- User gets consolidated feedback about multiple sources")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()