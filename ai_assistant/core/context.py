#!/usr/bin/env python3
"""
System Context Module

Provides current system context like date, time, timezone, and other relevant information
for the AI assistant to use in responses.
"""

import datetime
import platform
import os
import socket
from typing import Dict, Any
from ai_assistant.core.logging import get_logger

logger = get_logger('system_context')


class SystemContext:
    """Provides system and temporal context for the AI assistant"""
    
    def __init__(self):
        self.timezone = self._get_timezone()
        self.platform_info = self._get_platform_info()
    
    def _get_timezone(self) -> str:
        """Get system timezone"""
        try:
            # Try to get timezone from system
            import time
            return time.tzname[0] if time.daylight == 0 else time.tzname[1]
        except Exception:
            return "UTC"
    
    def _get_platform_info(self) -> Dict[str, str]:
        """Get platform information"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname()
        }
    
    def get_current_datetime(self) -> Dict[str, Any]:
        """Get comprehensive current date/time information"""
        now = datetime.datetime.now()
        
        return {
            "current_datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "month": now.strftime("%B"),
            "year": now.year,
            "timezone": self.timezone,
            "unix_timestamp": int(now.timestamp()),
            "formatted": now.strftime("%A, %B %d, %Y at %H:%M:%S"),
            "relative_info": self._get_relative_time_info(now)
        }
    
    def _get_relative_time_info(self, now: datetime.datetime) -> Dict[str, Any]:
        """Get relative time information"""
        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)
        yesterday = today - datetime.timedelta(days=1)
        
        # Time of day
        hour = now.hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Week info
        week_start = today - datetime.timedelta(days=today.weekday())
        week_end = week_start + datetime.timedelta(days=6)
        
        return {
            "time_of_day": time_of_day,
            "today": today.strftime("%Y-%m-%d"),
            "tomorrow": tomorrow.strftime("%Y-%m-%d"),
            "yesterday": yesterday.strftime("%Y-%m-%d"),
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "is_weekend": today.weekday() >= 5,
            "days_until_weekend": (5 - today.weekday()) % 7 if today.weekday() < 5 else 0
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            "platform": self.platform_info,
            "timezone": self.timezone,
            "working_directory": os.getcwd(),
            "user": os.getenv("USER", "unknown"),
            "home": os.getenv("HOME", "unknown"),
            "shell": os.getenv("SHELL", "unknown")
        }
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get complete system context"""
        context = {
            "timestamp": datetime.datetime.now().isoformat(),
            "datetime": self.get_current_datetime(),
            "system": self.get_system_info()
        }
        
        logger.debug(f"Generated system context at {context['timestamp']}")
        return context
    
    def get_context_summary(self) -> str:
        """Get a minimal context summary for AI prompts"""
        dt_info = self.get_current_datetime()
        
        # Keep it very simple - just essential time info
        return f"Today: {dt_info['date']} ({dt_info['day_of_week']}) at {dt_info['time']}"


# Global context instance
_context_instance = None

def get_system_context() -> SystemContext:
    """Get the global system context instance"""
    global _context_instance
    if _context_instance is None:
        _context_instance = SystemContext()
    return _context_instance


def get_context_for_ai() -> str:
    """Get context formatted for AI assistant prompts"""
    return get_system_context().get_context_summary()


def get_full_context_data() -> Dict[str, Any]:
    """Get full context data"""
    return get_system_context().get_full_context()