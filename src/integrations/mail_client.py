import subprocess
from typing import Dict, Any
from src.core.logging import get_logger

logger = get_logger('mail_app')

class MacMailClient:
    """Client for macOS Mail.app using AppleScript"""
    
    def __init__(self):
        self.accounts = []
        self._load_accounts()
    
    def _run_applescript(self, script: str, timeout: int = 10) -> str:
        """Execute AppleScript and return result"""
        cmd = ['osascript', '-e', script]
        logger.debug(f"Executing command: {' '.join(cmd[:2])} '{script}'")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=timeout)
            output = result.stdout.strip()
            
            logger.debug(f"AppleScript output: {output[:200]}{'...' if len(output) > 200 else ''}")
            return output
            
        except subprocess.TimeoutExpired:
            error_msg = f"Error: AppleScript timed out after {timeout} seconds"
            logger.error(f"AppleScript timeout: {error_msg}")
            logger.debug(f"Timed out script was: {script}")
            return error_msg
        except subprocess.CalledProcessError as e:
            error_msg = f"Error: {e.stderr.strip()}"
            logger.error(f"AppleScript failed: {error_msg}")
            logger.debug(f"Failed command was: {' '.join(cmd)}")
            return error_msg
    
    def _load_accounts(self):
        """Load available Mail accounts"""
        script = 'tell application "Mail" to get name of every account'
        result = self._run_applescript(script)
        if not result.startswith("Error:"):
            self.accounts = [acc.strip() for acc in result.split(',')]
    
    def get_accounts(self) -> Dict[str, Any]:
        """Get list of available accounts"""
        return {"accounts": self.accounts, "count": len(self.accounts)}
    
    def get_mailboxes(self, account_name: str = None) -> Dict[str, Any]:
        """Get mailboxes for an account"""
        if not account_name and self.accounts:
            account_name = self.accounts[0]
        
        if not account_name:
            return {"error": "No account specified and no accounts available"}
        
        try:
            account_index = self.accounts.index(account_name) + 1
        except ValueError:
            return {"error": f"Account '{account_name}' not found"}
        
        script = f'tell application "Mail" to get name of every mailbox of account {account_index}'
        result = self._run_applescript(script)
        
        if result.startswith("Error:"):
            return {"error": result}
        
        mailboxes = [mb.strip() for mb in result.split(',')]
        return {"mailboxes": mailboxes, "account": account_name}
    
    def search_messages(self, query: str = "", mailbox: str = "INBOX", 
                       account_name: str = None, limit: int = 10) -> Dict[str, Any]:
        """Search messages in Mail.app"""
        
        # If no account specified, search all accounts
        if not account_name:
            return self._search_all_accounts(query, mailbox, limit)
        
        try:
            account_index = self.accounts.index(account_name) + 1
        except ValueError:
            return {"error": f"Account '{account_name}' not found"}
        
        # Get message count first
        count_script = f'tell application "Mail" to get count of messages of mailbox "{mailbox}" of account {account_index}'
        count_result = self._run_applescript(count_script)
        
        if count_result.startswith("Error:"):
            return {"error": count_result}
        
        try:
            total_count = int(count_result)
            actual_limit = min(limit, total_count)
        except ValueError:
            return {"error": "Could not get message count"}
        
        messages = []
        for i in range(1, actual_limit + 1):
            # Get message details
            msg_script = f'''
            tell application "Mail"
                set msg to message {i} of mailbox "{mailbox}" of account {account_index}
                set msgSubject to subject of msg
                set msgSender to sender of msg
                set msgDate to date received of msg
                set msgRead to read status of msg
                return msgSubject & "|||" & msgSender & "|||" & (msgDate as string) & "|||" & (msgRead as string)
            end tell
            '''
            
            result = self._run_applescript(msg_script)
            if not result.startswith("Error:"):
                parts = result.split("|||")
                if len(parts) >= 4:
                    messages.append({
                        "index": i,
                        "subject": parts[0],
                        "sender": parts[1],
                        "date": parts[2],
                        "read": parts[3] == "true"
                    })
        
        # Filter by query if provided
        if query:
            query_lower = query.lower()
            messages = [msg for msg in messages if 
                       query_lower in msg["subject"].lower() or 
                       query_lower in msg["sender"].lower()]
        
        return {
            "messages": messages,
            "count": len(messages),
            "account": account_name,
            "mailbox": mailbox
        }
    
    def get_message_content(self, message_index: int, mailbox: str = "INBOX", 
                           account_name: str = None) -> Dict[str, Any]:
        """Get full content of a message"""
        if not account_name and self.accounts:
            account_name = self.accounts[0]
        
        try:
            account_index = self.accounts.index(account_name) + 1
        except ValueError:
            return {"error": f"Account '{account_name}' not found"}
        
        script = f'''
        tell application "Mail"
            set msg to message {message_index} of mailbox "{mailbox}" of account {account_index}
            set msgSubject to subject of msg
            set msgSender to sender of msg
            set msgDate to date received of msg
            set msgContent to content of msg
            return msgSubject & "|||" & msgSender & "|||" & (msgDate as string) & "|||" & msgContent
        end tell
        '''
        
        result = self._run_applescript(script)
        if result.startswith("Error:"):
            return {"error": result}
        
        parts = result.split("|||", 3)
        if len(parts) >= 4:
            return {
                "subject": parts[0],
                "sender": parts[1], 
                "date": parts[2],
                "content": parts[3],
                "index": message_index,
                "account": account_name,
                "mailbox": mailbox
            }
        
        return {"error": "Could not parse message content"}
    
    def send_message(self, to: str, subject: str, content: str, 
                    account_name: str = None) -> Dict[str, Any]:
        """Send a new message"""
        if not account_name and self.accounts:
            account_name = self.accounts[0]
        
        try:
            account_index = self.accounts.index(account_name) + 1
        except ValueError:
            return {"error": f"Account '{account_name}' not found"}
        
        # Escape quotes in content and handle newlines
        content_clean = content.replace('"', '\\"').replace("'", "\\'")
        subject_clean = subject.replace('"', '\\"').replace("'", "\\'")
        
        script = f'''
        tell application "Mail"
            set newMessage to make new outgoing message
            tell newMessage
                set subject to "{subject_clean}"
                set content to "{content_clean}"
                make new to recipient with properties {{address:"{to}"}}
                send
            end tell
        end tell
        '''
        
        result = self._run_applescript(script)
        if result.startswith("Error:"):
            return {"error": result, "sent": False}
        
        return {"sent": True, "to": to, "subject": subject, "account": account_name}
    
    def reply_to_message(self, message_index: int, content: str, 
                        mailbox: str = "INBOX", account_name: str = None) -> Dict[str, Any]:
        """Reply to a message"""
        if not account_name and self.accounts:
            account_name = self.accounts[0]
        
        try:
            account_index = self.accounts.index(account_name) + 1
        except ValueError:
            return {"error": f"Account '{account_name}' not found"}
        
        content_clean = content.replace('"', '\\"').replace("'", "\\'")
        
        script = f'''
        tell application "Mail"
            set originalMsg to message {message_index} of mailbox "{mailbox}" of account {account_index}
            set replyMsg to reply originalMsg with opening window
            set content of replyMsg to "{content_clean}"
            send replyMsg
        end tell
        '''
        
        result = self._run_applescript(script)
        if result.startswith("Error:"):
            return {"error": result, "reply_sent": False}
        
        return {"reply_sent": True, "message_index": message_index, "account": account_name}
    
    def _search_all_accounts(self, query: str = "", mailbox: str = "INBOX", limit: int = 10) -> Dict[str, Any]:
        """Search messages across all accounts"""
        all_messages = []
        searched_accounts = []
        per_account_limit = max(1, limit // len(self.accounts)) if self.accounts else limit
        
        for account in self.accounts:
            try:
                account_index = self.accounts.index(account) + 1
                
                # Get message count first
                count_script = f'tell application "Mail" to get count of messages of mailbox "{mailbox}" of account {account_index}'
                count_result = self._run_applescript(count_script)
                
                if count_result.startswith("Error:"):
                    continue
                
                try:
                    total_count = int(count_result)
                    actual_limit = min(per_account_limit, total_count)
                except ValueError:
                    continue
                
                searched_accounts.append(account)
                
                # Get messages from this account
                for i in range(1, actual_limit + 1):
                    msg_script = f'''
                    tell application "Mail"
                        set msg to message {i} of mailbox "{mailbox}" of account {account_index}
                        set msgSubject to subject of msg
                        set msgSender to sender of msg
                        set msgDate to date received of msg
                        set msgRead to read status of msg
                        return msgSubject & "|||" & msgSender & "|||" & (msgDate as string) & "|||" & (msgRead as string)
                    end tell
                    '''
                    
                    result = self._run_applescript(msg_script)
                    if not result.startswith("Error:"):
                        parts = result.split("|||")
                        if len(parts) >= 4:
                            message_data = {
                                "index": i,
                                "subject": parts[0],
                                "sender": parts[1],
                                "date": parts[2],
                                "read": parts[3] == "true",
                                "account": account
                            }
                            all_messages.append(message_data)
                            
            except Exception:
                continue
        
        # Filter by query if provided
        if query:
            query_lower = query.lower()
            all_messages = [msg for msg in all_messages if 
                           query_lower in msg["subject"].lower() or 
                           query_lower in msg["sender"].lower()]
        
        # Sort by date (most recent first) and limit
        all_messages.sort(key=lambda x: x["date"], reverse=True)
        limited_messages = all_messages[:limit]
        
        return {
            "messages": limited_messages,
            "count": len(limited_messages),
            "total_found": len(all_messages),
            "accounts_searched": searched_accounts,
            "accounts_count": len(searched_accounts),
            "query": query if query else "all messages"
        }

# Tool registry for Mac Mail
class MacMailTools:
    def __init__(self, mail_client: MacMailClient):
        self.mail = mail_client
        self.catalog = {
            "mail.accounts": {"args": {}},
            "mail.mailboxes": {"args": {"account_name": "string?"}},
            "mail.search": {"args": {"query": "string?", "mailbox": "string?", "account_name": "string?", "limit": "number?"}},
            "mail.get": {"args": {"message_index": "number", "mailbox": "string?", "account_name": "string?"}},
            "mail.send": {"args": {"to": "string", "subject": "string", "content": "string", "account_name": "string?"}},
            "mail.reply": {"args": {"message_index": "number", "content": "string", "mailbox": "string?", "account_name": "string?"}}
        }
    
    def call(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "mail.accounts":
                result = self.mail.get_accounts()
                return {"tool": name, "ok": "error" not in result, "data": result}
            
            elif name == "mail.mailboxes":
                result = self.mail.get_mailboxes(args.get("account_name"))
                return {"tool": name, "ok": "error" not in result, "data": result}
            
            elif name == "mail.search":
                result = self.mail.search_messages(
                    query=args.get("query", ""),
                    mailbox=args.get("mailbox", "INBOX"),
                    account_name=args.get("account_name"),
                    limit=args.get("limit", 10)
                )
                return {"tool": name, "ok": "error" not in result, "data": result}
            
            elif name == "mail.get":
                result = self.mail.get_message_content(
                    message_index=args["message_index"],
                    mailbox=args.get("mailbox", "INBOX"),
                    account_name=args.get("account_name")
                )
                return {"tool": name, "ok": "error" not in result, "data": result}
            
            elif name == "mail.send":
                result = self.mail.send_message(
                    to=args["to"],
                    subject=args["subject"],
                    content=args["content"],
                    account_name=args.get("account_name")
                )
                return {"tool": name, "ok": "error" not in result, "data": result}
            
            elif name == "mail.reply":
                result = self.mail.reply_to_message(
                    message_index=args["message_index"],
                    content=args["content"],
                    mailbox=args.get("mailbox", "INBOX"),
                    account_name=args.get("account_name")
                )
                return {"tool": name, "ok": "error" not in result, "data": result}
            
            else:
                return {"tool": name, "ok": False, "error": "unknown tool"}
                
        except Exception as e:
            return {"tool": name, "ok": False, "error": str(e)}