# assistant_generic_stepwise.py
# pip install anthropic
import json, datetime as dt, os
from anthropic import Anthropic

# ----- Logging configuration -----
from src.core.logging import setup_logging
from src.core.context import get_context_for_ai, get_full_context_data

logger = setup_logging('ai_assistant')

# ----- Mac Calendar.app integration -----
try:
    from src.integrations.calendar_client import MacCalendarClient, MacCalendarTools
    calendar_client = MacCalendarClient()
    calendar_tools = MacCalendarTools(calendar_client)
    CALENDAR_APP_AVAILABLE = True
except Exception as e:
    logger.warning(f"Calendar.app integration not available: {e}")
    CALENDAR_APP_AVAILABLE = False

# ----- Mac Mail.app integration -----
try:
    from src.integrations.mail_client import MacMailClient, MacMailTools
    mail_client = MacMailClient()
    mail_tools = MacMailTools(mail_client)
    MAIL_APP_AVAILABLE = True
except Exception as e:
    logger.warning(f"Mail.app integration not available: {e}")
    MAIL_APP_AVAILABLE = False

# ----- Tool registry with uniform interface -----
class Tools:
    def __init__(self):
        self.catalog = {}
        
        # Add Calendar.app tools if available
        if CALENDAR_APP_AVAILABLE:
            self.catalog.update({
                "calendar.list": {"args": {"calendar_name": "string?", "start_date": "string?", "end_date": "string?", "limit": "number?"}},
                "calendar.calendars": {"args": {}},
                "calendar.search": {"args": {"keyword": "string", "calendar_name": "string?"}},
                "calendar.create": {"args": {"title": "string", "start": "string", "end": "string", "calendar_name": "string?", "description": "string?"}},
                "calendar.delete": {"args": {"title": "string", "calendar_name": "string?"}}
            })
        
        # Add Mac Mail.app tools if available
        if MAIL_APP_AVAILABLE:
            self.catalog.update({
                "mail.accounts":     {"args": {}},
                "mail.mailboxes":    {"args": {"account_name": "string?"}},
                "mail.search":       {"args": {"query": "string?", "mailbox": "string?", "account_name": "string?", "limit": "number?"}},
                "mail.get":          {"args": {"message_index": "number", "mailbox": "string?", "account_name": "string?"}},
                "mail.send":         {"args": {"to": "string", "subject": "string", "content": "string", "account_name": "string?"}},
                "mail.reply":        {"args": {"message_index": "number", "content": "string", "mailbox": "string?", "account_name": "string?"}}
            })
    
    def call(self, name, args):
        try:
            # Calendar.app tools
            if CALENDAR_APP_AVAILABLE and name.startswith("calendar."):
                return calendar_tools.call(name, args)
            
            # Mac Mail.app tools
            if MAIL_APP_AVAILABLE and name.startswith("mail."):
                return mail_tools.call(name, args)
            
            return {"tool":name, "ok":False, "error":"unknown tool"}
        except Exception as e:
            return {"tool":name, "ok":False, "error":str(e)}

# ----- LLM helpers -----
def safe_json(txt: str):
    """Parse JSON with fallback strategies"""
    # First try direct parsing
    try: 
        return json.loads(txt)
    except json.JSONDecodeError as e:
        logger.debug(f"Direct JSON parse failed: {e}")
        logger.debug(f"Raw text: {repr(txt)}")
    
    # Try to extract JSON from text
    try:
        s = txt.find("{")
        e = txt.rfind("}")
        if s >= 0 and e > s: 
            extracted = txt[s:e+1]
            logger.debug(f"Extracted JSON: {extracted}")
            return json.loads(extracted)
    except json.JSONDecodeError as e:
        logger.debug(f"Extracted JSON parse failed: {e}")
    
    # Try to fix common issues
    try:
        # Remove leading/trailing whitespace and newlines
        cleaned = txt.strip()
        
        # Try to fix incomplete JSON by adding missing braces
        if cleaned.startswith('{') and not cleaned.endswith('}'):
            cleaned += '}'
            logger.debug(f"Added missing closing brace: {cleaned}")
            return json.loads(cleaned)
        
        # If starts with quote, might be incomplete string
        if cleaned.startswith('"') and not cleaned.endswith('"'):
            cleaned += '"'
            logger.debug(f"Added missing closing quote: {cleaned}")
            return json.loads(cleaned)
            
    except json.JSONDecodeError as e:
        logger.debug(f"Cleaned JSON parse failed: {e}")
    
    # Last resort: create error response
    logger.error(f"Failed to parse JSON from: {repr(txt)}")
    return {
        "next": {
            "type": "finalize", 
            "message": f"Sorry, I encountered a parsing error. The response was: {txt[:100]}..."
        },
        "needs_confirmation": False
    }

def llm(client: Anthropic, system: str, payload: dict, model="claude-3-5-sonnet-20241022", temperature=0.2):
    r = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=temperature,
        system=system,
        messages=[{"role":"user","content":json.dumps(payload, ensure_ascii=False)}]
    )
    return r.content[0].text

# ----- Prompts: plan one step at a time, no fixed filters -----
SYSTEM_ONE_STEP = """You are a tool-using assistant. Plan and execute tasks step-by-step.
Current context: {system_context}

Given the goal, available tools, and the latest observations:
- Choose ONE next action (a single tool call) OR finalize with a user-facing message.
- Do all selection/classification/reasoning yourself using the observations (no special filter tools).
- Consider current date/time when working with calendars, scheduling, or time-sensitive tasks.
- If proposing a destructive action (e.g., delete), set needs_confirmation=true first.
- IMPORTANT: If you've successfully retrieved data (even if empty/no results found), you should finalize rather than keep searching.
- IMPORTANT: Empty results from calendar or email searches are valid successful completions - report them to the user.

Return STRICT JSON:
{{
  "next": {{"type":"tool.call","name":"...","args":{{...}}}}
       | {{"type":"finalize","message":"..."}},
  "needs_confirmation": true|false
}}
Use only tools listed in tool_catalog. Keep args minimal.
"""

SYSTEM_FINALIZER = """Write a concise summary of what was done and any changes, using the observations. Return STRICT JSON:
{ "message": "..." }"""

# ----- Orchestrator: stepwise with latest observations every turn -----

def get_user_confirmation(message):
    """Get user confirmation for destructive actions"""
    print(f"\n⚠️  {message}")
    while True:
        response = input("Do you want to proceed? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print("Please enter 'y' or 'n'")

def interactive_chat():
    """Interactive chat interface with the AI assistant"""
    print("=== AI Assistant Chat ===")
    print("Type 'exit' or 'quit' to end the conversation")
    calendar_status = "Calendar.app: ✅" if CALENDAR_APP_AVAILABLE else "Calendar.app: ❌"
    mail_status = "Mail.app: ✅" if MAIL_APP_AVAILABLE else "Mail.app: ❌"
    print(f"Available actions: calendar ({calendar_status}), email ({mail_status})")
    
    if CALENDAR_APP_AVAILABLE:
        calendars = calendar_client.calendars[:5]  # Show first 5
        more = f" (+{len(calendar_client.calendars)-5} more)" if len(calendar_client.calendars) > 5 else ""
        print(f"Calendars: {', '.join(calendars)}{more}")
        logger.info(f"Calendar.app integration active with {len(calendar_client.calendars)} calendars")
    
    if MAIL_APP_AVAILABLE:
        accounts = mail_client.accounts
        print(f"Mail accounts: {', '.join(accounts)}")
        logger.info(f"Mail.app integration active with {len(accounts)} accounts")
    print()
    
    while True:
        goal = input("You: ").strip()
        
        if goal.lower() in ['exit', 'quit', 'bye']:
            print("Assistant: Goodbye!")
            logger.info("User ended conversation")
            break
            
        if not goal:
            continue
            
        logger.info(f"User query: {goal}")
        print("Assistant: Let me help you with that...")
        
        try:
            result = run(goal)
            print(f"\n✅ {result['summary']}")
            
            if result.get('observations'):
                print("\n📋 Actions taken:")
                for obs in result['observations']:
                    if obs.get('ok'):
                        tool = obs['tool']
                        data = obs['data']
                        logger.info(f"Tool {tool} executed successfully")
                        if tool == 'calendar.list':
                            events = data.get('events', [])
                            calendars_searched = data.get('calendars_searched', [])
                            if calendars_searched:
                                print(f"  • Listed {len(events)} events from {len(calendars_searched)} calendars")
                            else:
                                print(f"  • Listed {len(events)} calendar events")
                        elif tool == 'calendar.batchDelete':
                            count = data.get('count', 0)
                            print(f"  • Deleted {count} calendar events")
                        elif tool == 'calendar.create':
                            event = data.get('created', {})
                            print(f"  • Created event '{event.get('title', 'Unknown')}' (ID: {data.get('id', 'Unknown')})")
                        elif tool == 'calendar.update':
                            event = data.get('updated', {})
                            print(f"  • Updated event '{event.get('title', 'Unknown')}' (ID: {event.get('id', 'Unknown')})")
                        elif tool == 'calendar.getById':
                            event = data.get('event', {})
                            print(f"  • Retrieved event '{event.get('title', 'Unknown')}' (ID: {event.get('id', 'Unknown')})")
                        elif tool == 'calendar.search':
                            count = data.get('count', 0)
                            keyword = data.get('keyword', 'N/A')
                            calendars_searched = data.get('calendars_searched', [])
                            if calendars_searched:
                                print(f"  • Found {count} events matching '{keyword}' across {len(calendars_searched)} calendars")
                            else:
                                print(f"  • Found {count} events matching '{keyword}'")
                        elif tool == 'calendar.calendars':
                            calendars = data.get('calendars', [])
                            print(f"  • Found {len(calendars)} calendars")
                        elif tool == 'calendar.create':
                            created = data.get('created', False)
                            title = data.get('title', 'Unknown')
                            print(f"  • Calendar event {'created' if created else 'failed to create'}: '{title}'")
                        elif tool == 'calendar.delete':
                            deleted = data.get('deleted', False)
                            title = data.get('title', 'Unknown')
                            print(f"  • Calendar event {'deleted' if deleted else 'failed to delete'}: '{title}'")
                        elif tool == 'mail.accounts':
                            accounts = data.get('accounts', [])
                            print(f"  • Found {len(accounts)} Mail accounts: {', '.join(accounts)}")
                        elif tool == 'mail.mailboxes':
                            mailboxes = data.get('mailboxes', [])
                            account = data.get('account', 'Unknown')
                            print(f"  • Found {len(mailboxes)} mailboxes in {account}")
                        elif tool == 'mail.search':
                            count = data.get('count', 0)
                            accounts_searched = data.get('accounts_searched', [])
                            query = data.get('query', 'messages')
                            if accounts_searched:
                                print(f"  • Found {count} {query} across {len(accounts_searched)} accounts")
                            else:
                                account = data.get('account', 'Unknown')
                                mailbox = data.get('mailbox', 'Unknown')
                                print(f"  • Found {count} messages in {account}/{mailbox}")
                        elif tool == 'mail.get':
                            subject = data.get('subject', 'Unknown')
                            print(f"  • Retrieved message: '{subject[:50]}{'...' if len(subject) > 50 else ''}'")
                        elif tool == 'mail.send':
                            sent = data.get('sent', False)
                            to = data.get('to', 'Unknown')
                            print(f"  • Mail {'sent successfully' if sent else 'failed to send'} to {to}")
                        elif tool == 'mail.reply':
                            reply_sent = data.get('reply_sent', False)
                            print(f"  • Mail reply {'sent successfully' if reply_sent else 'failed to send'}")
                    else:
                        logger.error(f"Tool {obs['tool']} failed: {obs.get('error', 'Unknown error')}")
                        print(f"  • Error with {obs['tool']}: {obs.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ Sorry, I encountered an error: {str(e)}")
            logger.debug(f"Debug info: result = {result if 'result' in locals() else 'N/A'}")
            import traceback
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
        
        print("\n" + "-" * 50)

def run(goal: str, auto_confirm=True, max_steps=12):
    """Execute a goal using tool-calling AI assistant"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    client = Anthropic(api_key=api_key)
    tools = Tools()
    observations = []

    for _ in range(max_steps):
        # Create view with minimal context
        context_info = get_context_for_ai()
        view = {"goal": goal, "tool_catalog": tools.catalog, "observations": observations}
        
        # Get step from AI
        system_prompt = SYSTEM_ONE_STEP.format(system_context=context_info)
        step = safe_json(llm(client, system_prompt, view))
        logger.debug(f"Step: {json.dumps(step, indent=2)}")

        # Handle direct finalize response (AI didn't wrap it in "next")
        if step.get("type") == "finalize":
            return {"summary": step["message"], "observations": observations}

        # Finalize?
        if step.get("next", {}).get("type") == "finalize":
            final = safe_json(llm(client, SYSTEM_FINALIZER, {"goal": goal, "observations": observations}))
            return {"summary": final["message"], "observations": observations}

        # Ensure we have a "next" key for tool execution
        if "next" not in step:
            logger.warning(f"No 'next' key in step: {step}")
            return {"summary": "Invalid response from AI - missing action", "observations": observations}

        # Confirmation gate for destructive operations
        if step.get("needs_confirmation") and not auto_confirm:
            action_desc = f"{step['next']['name']} with args {step['next'].get('args', {})}"
            if not get_user_confirmation(f"Confirm: {action_desc}"):
                observations.append({"tool": "confirmation", "ok": False, "error": "user declined"})
                continue

        # Execute exactly ONE action, then loop so the model sees the fresh observation
        if step["next"]["type"] == "tool.call":
            name = step["next"]["name"]
            args = step["next"].get("args", {})
            logger.info(f"Executing: {name}({args})")
            obs = tools.call(name, args)
            observations.append(obs)

    # Fallback if budget reached
    return {"summary": "Stopped due to step budget.", "observations": observations}


if __name__ == "__main__":
    interactive_chat()