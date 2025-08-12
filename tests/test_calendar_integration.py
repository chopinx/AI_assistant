#!/usr/bin/env python3
"""
Test Mac Calendar.app Integration

This script tests the Mac Calendar.app client functionality.
"""

from src.integrations.calendar_client import MacCalendarClient, MacCalendarTools
import json
from src.core.logging import get_logger

logger = get_logger('test_calendar')

def test_calendar():
    """Test Calendar.app functionality"""
    print("🧪 Testing Mac Calendar.app Integration")
    print("-" * 40)
    
    # Initialize client
    calendar_client = MacCalendarClient()
    calendar_tools = MacCalendarTools(calendar_client)
    
    # Test calendars list
    print("1. Testing calendars list...")
    calendars_result = calendar_tools.call("calendar.calendars", {})
    print(f"   Result: {calendars_result}")
    
    if calendars_result["ok"]:
        calendars = calendars_result["data"]["calendars"]
        print(f"✅ Found {len(calendars)} calendars")
        print(f"   Calendars: {', '.join(calendars[:5])}{'...' if len(calendars) > 5 else ''}")
        
        # Find a suitable calendar for testing
        work_calendar = None
        for cal in calendars:
            if "Work" in cal:
                work_calendar = cal
                break
        
        if not work_calendar:
            # Use first non-holiday calendar
            for cal in calendars:
                if "Holiday" not in cal and "Birthday" not in cal:
                    work_calendar = cal
                    break
        
        # Test listing events from all calendars (new consolidated feature)
        print(f"\n2. Testing consolidated event list (all calendars)...")
        list_all_result = calendar_tools.call("calendar.list", {
            "limit": 5  # No calendar_name specified = search all
        })
        
        if list_all_result["ok"]:
            data = list_all_result["data"]
            events = data.get("events", [])
            calendars_searched = data.get("calendars_searched", [])
            
            print(f"   ✅ Found {len(events)} events across {len(calendars_searched)} calendars")
            print(f"   📅 Calendars searched: {', '.join(calendars_searched[:3])}...")
            
            # Show first few events with their calendar names
            for i, event in enumerate(events[:3], 1):
                print(f"   {i}. {event['title']} ({event['calendar']})")
                print(f"      Start: {event['start']}")
        else:
            print(f"   ❌ Error: {list_all_result['data'].get('error', 'Unknown')}")
        
        # Test consolidated search (new feature)
        print(f"\n3. Testing consolidated search across all calendars...")
        search_all_result = calendar_tools.call("calendar.search", {
            "keyword": "面试"  # Chinese for "interview" - no calendar_name = search all
        })
        
        if search_all_result["ok"]:
            data = search_all_result["data"]
            search_events = data.get("events", [])
            calendars_searched = data.get("calendars_searched", [])
            keyword = data.get("keyword", "面试")
            
            print(f"   ✅ Found {len(search_events)} events matching '{keyword}' across {len(calendars_searched)} calendars")
            
            for event in search_events[:2]:
                print(f"   - {event['title']} in {event['calendar']} on {event['start']}")
        else:
            print(f"   ❌ Error: {search_all_result['data'].get('error', 'Unknown')}")
        
        # Test specific calendar (legacy functionality still works)
        if work_calendar:
            print(f"\n4. Testing specific calendar '{work_calendar}'...")
            specific_result = calendar_tools.call("calendar.list", {
                "calendar_name": work_calendar,
                "limit": 3
            })
            
            if specific_result["ok"]:
                events = specific_result["data"]["events"]
                print(f"   Found {len(events)} events in {work_calendar}")
                
                for i, event in enumerate(events[:2], 1):
                    print(f"   {i}. {event['title']}")
            else:
                print(f"   Error: {specific_result['data'].get('error', 'Unknown')}")
    
    print("\n✅ Mac Calendar.app integration test completed!")
    return True

def interactive_test():
    """Interactive test mode"""
    calendar_client = MacCalendarClient()
    calendar_tools = MacCalendarTools(calendar_client)
    
    print("🔧 Interactive Mac Calendar Test Mode")
    print("Available commands: calendars, list, search, create, delete, quit")
    print("💡 TIP: Leave calendar name empty to search ALL calendars!")
    
    while True:
        command = input("\nEnter command: ").strip().lower()
        
        if command == "quit":
            break
        elif command == "calendars":
            result = calendar_tools.call("calendar.calendars", {})
            print(json.dumps(result, indent=2))
        elif command == "list":
            calendar_name = input("Calendar name (press Enter to search ALL calendars): ").strip()
            start_date = input("Start date YYYY-MM-DD (optional): ").strip()
            end_date = input("End date YYYY-MM-DD (optional): ").strip()
            limit = input("Limit (default 10): ").strip()
            
            args = {
                "limit": int(limit) if limit else 10
            }
            if calendar_name:
                args["calendar_name"] = calendar_name
                print(f"📅 Searching calendar: {calendar_name}")
            else:
                print("📅 Searching ALL calendars...")
                
            if start_date:
                args["start_date"] = start_date
            if end_date:
                args["end_date"] = end_date
                
            result = calendar_tools.call("calendar.list", args)
            
            # Pretty print the consolidated results
            if result["ok"]:
                data = result["data"]
                events = data.get("events", [])
                calendars_searched = data.get("calendars_searched", [])
                
                print(f"\n✅ Results: {len(events)} events")
                if calendars_searched:
                    print(f"📊 Searched {len(calendars_searched)} calendars: {', '.join(calendars_searched[:3])}...")
                
                for i, event in enumerate(events, 1):
                    calendar_info = f" ({event['calendar']})" if 'calendar' in event else ""
                    print(f"{i}. {event['title']}{calendar_info}")
                    print(f"   {event['start']} - {event['end']}")
            else:
                print(json.dumps(result, indent=2))
        elif command == "search":
            keyword = input("Search keyword: ")
            calendar_name = input("Calendar name (press Enter to search ALL calendars): ").strip()
            
            args = {"keyword": keyword}
            if calendar_name:
                args["calendar_name"] = calendar_name
                print(f"🔍 Searching calendar: {calendar_name}")
            else:
                print("🔍 Searching ALL calendars...")
                
            result = calendar_tools.call("calendar.search", args)
            
            # Pretty print the consolidated search results
            if result["ok"]:
                data = result["data"]
                events = data.get("events", [])
                calendars_searched = data.get("calendars_searched", [])
                keyword_used = data.get("keyword", keyword)
                
                print(f"\n✅ Results: {len(events)} events matching '{keyword_used}'")
                if calendars_searched:
                    print(f"📊 Searched {len(calendars_searched)} calendars: {', '.join(calendars_searched[:3])}...")
                
                for i, event in enumerate(events, 1):
                    calendar_info = f" ({event['calendar']})" if 'calendar' in event else ""
                    print(f"{i}. {event['title']}{calendar_info}")
                    print(f"   {event['start']}")
            else:
                print(json.dumps(result, indent=2))
        elif command == "create":
            title = input("Event title: ")
            start = input("Start date/time (e.g., '2024-12-25 14:00' or 'tomorrow 2pm'): ")
            end = input("End date/time: ")
            calendar_name = input("Calendar name (optional): ").strip()
            description = input("Description (optional): ").strip()
            
            args = {
                "title": title,
                "start": start,
                "end": end
            }
            if calendar_name:
                args["calendar_name"] = calendar_name
            if description:
                args["description"] = description
                
            result = calendar_tools.call("calendar.create", args)
            print(json.dumps(result, indent=2))
        elif command == "delete":
            title = input("Event title to delete: ")
            calendar_name = input("Calendar name (optional): ").strip()
            
            args = {"title": title}
            if calendar_name:
                args["calendar_name"] = calendar_name
                
            result = calendar_tools.call("calendar.delete", args)
            print(json.dumps(result, indent=2))
        else:
            print("Unknown command. Available: calendars, list, search, create, delete, quit")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        test_calendar()