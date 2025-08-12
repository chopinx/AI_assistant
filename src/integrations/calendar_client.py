import subprocess
import datetime
import re
import json
import os
from typing import Dict, Any, List, Optional
from src.core.logging import get_logger

logger = get_logger("calendar_app")


class MacCalendarClient:
    """Client for macOS Calendar.app using AppleScript"""

    def __init__(self, config_path: str = "config/calendar_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.calendars = []
        self.enabled_calendars = []
        self._load_calendars()

    def _load_config(self) -> Dict[str, Any]:
        """Load calendar configuration from JSON file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                logger.debug(f"Loaded calendar config from {self.config_path}")
                return config.get("calendar_settings", {})
            else:
                logger.warning(
                    f"Config file {self.config_path} not found, using defaults"
                )
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "enabled_calendars": {},
            "disabled_calendars": ["Holiday", "Birthday", "Siri Suggestions"],
            "default_enabled": True,
            "timeout_seconds": 15,
            "skip_patterns": ["Holiday", "Birthday", "Siri"],
        }

    def _save_config(self):
        """Save current configuration to file"""
        try:
            config_data = {"calendar_settings": self.config}
            with open(self.config_path, "w") as f:
                json.dump(config_data, f, indent=2)
            logger.debug(f"Saved calendar config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def _is_calendar_enabled(self, calendar_name: str) -> bool:
        """Check if a calendar is enabled based on configuration"""
        # Check if explicitly disabled
        if calendar_name in self.config.get("disabled_calendars", []):
            return False

        # Check skip patterns
        for pattern in self.config.get("skip_patterns", []):
            if pattern in calendar_name:
                return False

        # Check explicit enabled/disabled setting
        enabled_calendars = self.config.get("enabled_calendars", {})
        if calendar_name in enabled_calendars:
            return enabled_calendars[calendar_name]

        # Use default setting
        return self.config.get("default_enabled", True)

    def enable_calendar(self, calendar_name: str):
        """Enable a specific calendar"""
        if "enabled_calendars" not in self.config:
            self.config["enabled_calendars"] = {}
        self.config["enabled_calendars"][calendar_name] = True
        self._save_config()
        self._update_enabled_calendars()
        logger.info(f"Enabled calendar: {calendar_name}")

    def disable_calendar(self, calendar_name: str):
        """Disable a specific calendar"""
        if "enabled_calendars" not in self.config:
            self.config["enabled_calendars"] = {}
        self.config["enabled_calendars"][calendar_name] = False
        self._save_config()
        self._update_enabled_calendars()
        logger.info(f"Disabled calendar: {calendar_name}")

    def _update_enabled_calendars(self):
        """Update the list of enabled calendars"""
        self.enabled_calendars = [
            cal for cal in self.calendars if self._is_calendar_enabled(cal)
        ]
        logger.debug(
            f"Updated enabled calendars: {len(self.enabled_calendars)}/{len(self.calendars)}"
        )

    def _parse_applescript_events(
        self, result: str, calendar_name: str
    ) -> List[Dict[str, Any]]:
        """Parse AppleScript event output with improved error handling"""
        events = []
        try:
            # Handle empty result
            if not result or result.strip() == "":
                return events

            logger.debug(f"Raw AppleScript result: {result}")

            # First, check if this is a single event or multiple events
            # Single events have format: title||start||end||desc
            # Multiple events are separated by ", " between complete events

            # Count the number of || delimiters - should be multiple of 3 (or 4 if descriptions)
            pipe_count = result.count("||")

            if pipe_count == 3:
                # This is likely a single event: title||start||end||description
                logger.debug("Detected single event format")
                potential_events = [result]
            else:
                # Multiple events - need to split carefully
                # Strategy: Split on ", " and reconstruct events by counting || delimiters
                # Each complete event should have exactly 3 || separators
                
                potential_events = []
                current_event = ""
                parts = result.split(", ")
                
                for i, part in enumerate(parts):
                    if current_event:
                        current_event += ", " + part
                    else:
                        current_event = part
                    
                    # Check if this completes an event (should have 3 || separators)
                    if current_event.count("||") >= 3:
                        # Check if the next part (if exists) starts a new event
                        if i + 1 < len(parts):
                            next_part = parts[i + 1]
                            # If next part contains || near the beginning, it's likely a new event
                            if "||" in next_part and next_part.find("||") < 50:
                                potential_events.append(current_event)
                                current_event = ""
                        else:
                            # Last part
                            potential_events.append(current_event)
                            current_event = ""
                
                # Add any remaining event
                if current_event:
                    potential_events.append(current_event)
                    
                logger.debug("Split into events using iterative parsing")

            logger.debug(f"Processing {len(potential_events)} events")

            for i, event_str in enumerate(potential_events):
                try:
                    event_str = event_str.strip()
                    if not event_str:
                        continue

                    logger.debug(f"Processing event string: {event_str[:100]}...")

                    # Split by || to get event components
                    parts = event_str.split("||")

                    if len(parts) >= 4:
                        title = parts[0].strip()
                        start_str = parts[1].strip()
                        end_str = parts[2].strip()
                        description = parts[3].strip() if len(parts) > 3 else ""

                        # Handle missing values
                        if description == "missing value":
                            description = ""

                        # Basic validation - ensure we have title and start time
                        if title and start_str:
                            event = {
                                "id": f"{calendar_name}_{len(events) + 1}",
                                "title": title,
                                "start": start_str,
                                "end": end_str,
                                "description": description,
                                "calendar": calendar_name,
                            }
                            events.append(event)
                            logger.debug(
                                f"Successfully parsed event: '{title}' on {start_str}"
                            )
                        else:
                            logger.warning(
                                f"Invalid event - missing title or start: title='{title}', start='{start_str}'"
                            )

                    elif len(parts) >= 3:
                        # Handle events without description
                        title = parts[0].strip()
                        start_str = parts[1].strip()
                        end_str = parts[2].strip()

                        if title and start_str:
                            event = {
                                "id": f"{calendar_name}_{len(events) + 1}",
                                "title": title,
                                "start": start_str,
                                "end": end_str,
                                "description": "",
                                "calendar": calendar_name,
                            }
                            events.append(event)
                            logger.debug(
                                f"Successfully parsed event (no desc): '{title}' on {start_str}"
                            )
                    else:
                        logger.warning(
                            f"Insufficient parts in event string: {event_str[:50]}... (got {len(parts)} parts)"
                        )

                except Exception as e:
                    logger.error(
                        f"Error parsing individual event '{event_str[:50]}...': {e}"
                    )
                    continue

        except Exception as e:
            logger.error(f"Error parsing AppleScript result from {calendar_name}: {e}")

        logger.info(f"Successfully parsed {len(events)} events from {calendar_name}")
        return events

    def _parse_dates_for_applescript(
        self, start_date: str, end_date: str
    ) -> Dict[str, Any]:
        """Parse dates into AppleScript-compatible format consistently"""
        # Get current date if no dates specified
        if not start_date:
            start_date = datetime.date.today().strftime("%Y-%m-%d")
        if not end_date:
            end_date = (datetime.date.today() + datetime.timedelta(days=30)).strftime(
                "%Y-%m-%d"
            )

        # Parse dates for AppleScript
        start_parts = start_date.split("-")
        end_parts = end_date.split("-")
        start_year, start_month, start_day = (
            int(start_parts[0]),
            int(start_parts[1]),
            int(start_parts[2]),
        )
        end_year, end_month, end_day = (
            int(end_parts[0]),
            int(end_parts[1]),
            int(end_parts[2]),
        )

        # Convert month numbers to month names
        month_names = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        start_month_name = month_names[start_month - 1]
        end_month_name = month_names[end_month - 1]

        return {
            "start_date": start_date,
            "end_date": end_date,
            "start_year": start_year,
            "start_month": start_month,
            "start_day": start_day,
            "start_month_name": start_month_name,
            "end_year": end_year,
            "end_month": end_month,
            "end_day": end_day,
            "end_month_name": end_month_name,
        }

    def _generate_applescript_event_query(
        self, calendar_name: str, date_params: Dict[str, Any]
    ) -> str:
        """Generate standardized AppleScript for querying events"""
        return f"""
        tell application "Calendar"
            set targetCalendar to calendar "{calendar_name}"
            
            -- Construct start date: {date_params["start_date"]} 00:00:00
            set startDate to current date
            set year of startDate to {date_params["start_year"]}
            set month of startDate to {date_params["start_month_name"]}
            set day of startDate to {date_params["start_day"]}
            set time of startDate to 0
            
            -- Construct end date: {date_params["end_date"]} 23:59:59
            set endDate to current date
            set year of endDate to {date_params["end_year"]}
            set month of endDate to {date_params["end_month_name"]}
            set day of endDate to {date_params["end_day"]}
            set time of endDate to (24 * hours - 1)
            
            set eventList to {{}}
            
            -- Use intersection logic: start < endDate AND end > startDate
            set evs to (every event of targetCalendar whose ((start date) < endDate) and ((end date) > startDate))
            
            repeat with anEvent in evs
                set eventTitle to summary of anEvent
                set eventStart to (start date of anEvent) as string
                set eventEnd to (end date of anEvent) as string
                set eventDesc to description of anEvent
                
                -- Handle missing values
                if eventTitle is missing value then set eventTitle to ""
                if eventDesc is missing value then set eventDesc to ""
                
                -- Create structured format: TITLE||START||END||DESC
                set eventInfo to eventTitle & "||" & eventStart & "||" & eventEnd & "||" & eventDesc
                set end of eventList to eventInfo
            end repeat
            
            return eventList
        end tell
        """

    def get_events_for_ai(
        self,
        calendar_name: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 20,
    ) -> str:
        """Get events formatted for AI processing"""
        result = self.list_events(calendar_name, start_date, end_date, limit)

        if "error" in result:
            return f"Error retrieving events: {result['error']}"

        events = result.get("events", [])
        if not events:
            scope = (
                f"calendar '{calendar_name}'"
                if calendar_name
                else "all enabled calendars"
            )
            calendars_searched = result.get("calendars_searched", [])
            if calendars_searched:
                scope += f" (searched {len(calendars_searched)} calendars: {', '.join(calendars_searched)})"
            return f"No events found in {scope} for the specified date range. This is a complete and successful search result."

        # Format for AI consumption
        formatted_events = []
        for event in events:
            event_str = f"• {event['title']}"
            if event.get("start"):
                event_str += f" ({event['start']}"
                if event.get("end"):
                    event_str += f" - {event['end']}"
                event_str += ")"
            if event.get("description"):
                event_str += f" - {event['description']}"
            if event.get("calendar"):
                event_str += f" [{event['calendar']}]"
            formatted_events.append(event_str)

        summary = f"Found {len(events)} events"
        if result.get("calendars_searched"):
            summary += f" across {len(result['calendars_searched'])} calendars"
        if calendar_name:
            summary += f" in '{calendar_name}'"

        return f"{summary}:\n" + "\n".join(formatted_events)

    def _run_applescript(self, script: str, timeout: int = 15) -> str:
        """Execute AppleScript and return result"""
        cmd = ["osascript", "-e", script]
        logger.debug(f"Executing command: {' '.join(cmd[:2])} '{script}'")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=timeout
            )
            output = result.stdout.strip()

            logger.debug(
                f"AppleScript output: {output[:200]}{'...' if len(output) > 200 else ''}"
            )
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

    def _load_calendars(self):
        """Load available Calendar calendars and filter by configuration"""
        script = 'tell application "Calendar" to get name of every calendar'
        result = self._run_applescript(script)
        if not result.startswith("Error:"):
            self.calendars = [cal.strip() for cal in result.split(",")]
            self._update_enabled_calendars()
            logger.info(
                f"Loaded {len(self.calendars)} total calendars, {len(self.enabled_calendars)} enabled"
            )

    def get_calendars(self) -> Dict[str, Any]:
        """Get list of available calendars with enabled/disabled status"""
        calendar_status = []
        for cal in self.calendars:
            calendar_status.append(
                {"name": cal, "enabled": self._is_calendar_enabled(cal)}
            )

        return {
            "calendars": self.calendars,
            "enabled_calendars": self.enabled_calendars,
            "calendar_status": calendar_status,
            "total_count": len(self.calendars),
            "enabled_count": len(self.enabled_calendars),
        }

    def list_events(
        self,
        calendar_name: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """List events from Calendar.app"""

        # If no calendar specified, search all calendars
        if not calendar_name:
            return self._list_all_calendars(start_date, end_date, limit)

        if calendar_name not in self.calendars:
            return {"error": f"Calendar '{calendar_name}' not found"}

        # Use centralized date parsing
        date_params = self._parse_dates_for_applescript(start_date, end_date)

        # Generate standardized AppleScript
        script = self._generate_applescript_event_query(calendar_name, date_params)

        result = self._run_applescript(script)
        if result.startswith("Error:"):
            return {"error": result}

        # Use improved parsing method
        all_events = self._parse_applescript_events(result, calendar_name)
        events = all_events[:limit] if limit else all_events

        return {"events": events, "count": len(events), "calendar": calendar_name}

    def search_events(self, keyword: str, calendar_name: str = None) -> Dict[str, Any]:
        """Search events by keyword"""
        if not calendar_name:
            # Search all calendars
            return self._search_all_calendars(keyword)
        else:
            # Search specific calendar
            result = self.list_events(calendar_name, limit=100)
            if "error" in result:
                return result

            keyword_lower = keyword.lower()
            matching_events = []
            for event in result["events"]:
                if (
                    keyword_lower in event["title"].lower()
                    or keyword_lower in event.get("description", "").lower()
                ):
                    matching_events.append(event)

            return {
                "events": matching_events,
                "count": len(matching_events),
                "calendar": calendar_name,
                "keyword": keyword,
            }

    def create_event(
        self,
        title: str,
        start: str,
        end: str,
        calendar_name: str = None,
        description: str = "",
    ) -> Dict[str, Any]:
        """Create a new event in Calendar.app"""
        if not calendar_name and self.calendars:
            # Use first writable calendar
            for cal in self.calendars:
                if "Holiday" not in cal and "Birthday" not in cal and "Siri" not in cal:
                    calendar_name = cal
                    break

        if not calendar_name:
            return {"error": "No calendar specified"}

        if calendar_name not in self.calendars:
            return {"error": f"Calendar '{calendar_name}' not found"}

        # Parse dates - assume format like "2024-12-25 14:00" or "tomorrow 2pm"
        try:
            # Simple date parsing for common formats
            if "tomorrow" in start.lower():
                start_dt = datetime.datetime.now() + datetime.timedelta(days=1)
                if "pm" in start.lower() or "am" in start.lower():
                    # Extract time
                    time_match = re.search(r"(\d+)\s*(am|pm)", start.lower())
                    if time_match:
                        hour = int(time_match.group(1))
                        if time_match.group(2) == "pm" and hour != 12:
                            hour += 12
                        elif time_match.group(2) == "am" and hour == 12:
                            hour = 0
                        start_dt = start_dt.replace(hour=hour, minute=0, second=0)
                start_str = start_dt.strftime("%d/%m/%Y %H:%M:%S")
            else:
                # Try parsing as ISO format or other common formats
                try:
                    if "T" in start:
                        start_dt = datetime.datetime.fromisoformat(
                            start.replace("T", " ")
                        )
                    else:
                        start_dt = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M")
                    start_str = start_dt.strftime("%d/%m/%Y %H:%M:%S")
                except ValueError:
                    start_str = start  # Use as-is if parsing fails

            # Similar for end time
            if "tomorrow" in end.lower():
                end_dt = datetime.datetime.now() + datetime.timedelta(days=1)
                if "pm" in end.lower() or "am" in end.lower():
                    time_match = re.search(r"(\d+)\s*(am|pm)", end.lower())
                    if time_match:
                        hour = int(time_match.group(1))
                        if time_match.group(2) == "pm" and hour != 12:
                            hour += 12
                        elif time_match.group(2) == "am" and hour == 12:
                            hour = 0
                        end_dt = end_dt.replace(hour=hour, minute=0, second=0)
                end_str = end_dt.strftime("%d/%m/%Y %H:%M:%S")
            else:
                try:
                    if "T" in end:
                        end_dt = datetime.datetime.fromisoformat(end.replace("T", " "))
                    else:
                        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M")
                    end_str = end_dt.strftime("%d/%m/%Y %H:%M:%S")
                except ValueError:
                    end_str = end
        except ValueError:
            return {"error": f"Could not parse dates: {start}, {end}"}

        script = f"""
        tell application "Calendar"
            set targetCalendar to calendar "{calendar_name}"
            set startDate to date "{start_str}"
            set endDate to date "{end_str}"
            
            tell targetCalendar
                make new event with properties {{summary:"{title}", start date:startDate, end date:endDate, description:"{description}"}}
            end tell
        end tell
        """

        result = self._run_applescript(script)
        if result.startswith("Error:"):
            return {"error": result, "created": False}

        return {
            "created": True,
            "title": title,
            "start": start_str,
            "end": end_str,
            "calendar": calendar_name,
        }

    def delete_event(self, title: str, calendar_name: str = None) -> Dict[str, Any]:
        """Delete an event by title (first match)"""
        if not calendar_name and self.calendars:
            calendar_name = self.calendars[0]

        if calendar_name not in self.calendars:
            return {"error": f"Calendar '{calendar_name}' not found"}

        script = f"""
        tell application "Calendar"
            set targetCalendar to calendar "{calendar_name}"
            set foundEvent to first event of targetCalendar whose summary is "{title}"
            delete foundEvent
        end tell
        """

        result = self._run_applescript(script)
        if result.startswith("Error:"):
            return {"error": result, "deleted": False}

        return {"deleted": True, "title": title, "calendar": calendar_name}

    def _list_all_calendars(
        self, start_date: str = None, end_date: str = None, limit: int = 20
    ) -> Dict[str, Any]:
        """List events from all enabled calendars"""
        logger.info(
            f"Starting consolidated calendar search across {len(self.enabled_calendars)} enabled calendars"
        )

        all_events = []
        searched_calendars = []

        # Use centralized date parsing
        date_params = self._parse_dates_for_applescript(start_date, end_date)
        logger.debug(
            f"Search date range: {date_params['start_date']} to {date_params['end_date']}"
        )

        for cal in self.enabled_calendars:
            try:
                # Generate standardized AppleScript
                script = self._generate_applescript_event_query(cal, date_params)

                result = self._run_applescript(script)
                if not result.startswith("Error:"):
                    searched_calendars.append(cal)

                    if result and result != "":
                        # Parse improved format with better error handling
                        events = self._parse_applescript_events(result, cal)
                        all_events.extend(events)
            except Exception:
                # Skip problematic calendars
                continue

        # Sort by start date and limit results
        all_events.sort(key=lambda x: x["start"])
        limited_events = all_events[:limit]

        return {
            "events": limited_events,
            "count": len(limited_events),
            "total_found": len(all_events),
            "calendars_searched": searched_calendars,
            "calendars_count": len(searched_calendars),
        }

    def _search_all_calendars(self, keyword: str) -> Dict[str, Any]:
        """Search for keyword across all enabled calendars"""
        all_events = []
        searched_calendars = []
        keyword_lower = keyword.lower()

        for cal in self.enabled_calendars:

            try:
                # Get events from this calendar
                result = self.list_events(cal, limit=100)
                if "events" in result:
                    searched_calendars.append(cal)

                    # Filter by keyword
                    for event in result["events"]:
                        if (
                            keyword_lower in event["title"].lower()
                            or keyword_lower in event.get("description", "").lower()
                        ):
                            all_events.append(event)
            except Exception:
                # Skip problematic calendars
                continue

        # Sort by start date
        all_events.sort(key=lambda x: x["start"])

        return {
            "events": all_events,
            "count": len(all_events),
            "keyword": keyword,
            "calendars_searched": searched_calendars,
            "calendars_count": len(searched_calendars),
        }


# Tool registry for Mac Calendar
class MacCalendarTools:
    def __init__(self, calendar_client: MacCalendarClient):
        self.calendar = calendar_client
        self.catalog = {
            "calendar.list": {
                "args": {
                    "calendar_name": "string?",
                    "start_date": "string?",
                    "end_date": "string?",
                    "limit": "number?",
                }
            },
            "calendar.list_ai": {
                "args": {
                    "calendar_name": "string?",
                    "start_date": "string?",
                    "end_date": "string?",
                    "limit": "number?",
                }
            },
            "calendar.calendars": {"args": {}},
            "calendar.search": {
                "args": {"keyword": "string", "calendar_name": "string?"}
            },
            "calendar.create": {
                "args": {
                    "title": "string",
                    "start": "string",
                    "end": "string",
                    "calendar_name": "string?",
                    "description": "string?",
                }
            },
            "calendar.delete": {
                "args": {"title": "string", "calendar_name": "string?"}
            },
            "calendar.enable": {"args": {"calendar_name": "string"}},
            "calendar.disable": {"args": {"calendar_name": "string"}},
            "calendar.config": {"args": {}},
        }

    def call(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "calendar.calendars":
                result = self.calendar.get_calendars()
                return {"tool": name, "ok": "error" not in result, "data": result}

            elif name == "calendar.list":
                result = self.calendar.list_events(
                    calendar_name=args.get("calendar_name"),
                    start_date=args.get("start_date"),
                    end_date=args.get("end_date"),
                    limit=args.get("limit", 20),
                )
                return {"tool": name, "ok": "error" not in result, "data": result}

            elif name == "calendar.list_ai":
                result = self.calendar.get_events_for_ai(
                    calendar_name=args.get("calendar_name"),
                    start_date=args.get("start_date"),
                    end_date=args.get("end_date"),
                    limit=args.get("limit", 20),
                )
                return {"tool": name, "ok": True, "data": {"formatted_events": result}}

            elif name == "calendar.search":
                result = self.calendar.search_events(
                    keyword=args["keyword"], calendar_name=args.get("calendar_name")
                )
                return {"tool": name, "ok": "error" not in result, "data": result}

            elif name == "calendar.create":
                result = self.calendar.create_event(
                    title=args["title"],
                    start=args["start"],
                    end=args["end"],
                    calendar_name=args.get("calendar_name"),
                    description=args.get("description", ""),
                )
                return {"tool": name, "ok": "error" not in result, "data": result}

            elif name == "calendar.delete":
                result = self.calendar.delete_event(
                    title=args["title"], calendar_name=args.get("calendar_name")
                )
                return {"tool": name, "ok": "error" not in result, "data": result}

            elif name == "calendar.enable":
                self.calendar.enable_calendar(args["calendar_name"])
                return {
                    "tool": name,
                    "ok": True,
                    "data": {"calendar_name": args["calendar_name"], "enabled": True},
                }

            elif name == "calendar.disable":
                self.calendar.disable_calendar(args["calendar_name"])
                return {
                    "tool": name,
                    "ok": True,
                    "data": {"calendar_name": args["calendar_name"], "enabled": False},
                }

            elif name == "calendar.config":
                config_data = {
                    "config": self.calendar.config,
                    "total_calendars": len(self.calendar.calendars),
                    "enabled_calendars": len(self.calendar.enabled_calendars),
                    "calendar_status": [
                        {
                            "name": cal,
                            "enabled": self.calendar._is_calendar_enabled(cal),
                        }
                        for cal in self.calendar.calendars
                    ],
                }
                return {"tool": name, "ok": True, "data": config_data}

            else:
                return {"tool": name, "ok": False, "error": "unknown tool"}

        except Exception as e:
            return {"tool": name, "ok": False, "error": str(e)}
