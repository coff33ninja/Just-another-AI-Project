"""
Time Plugin - Get current time and date
"""

from plugins import Plugin
from typing import Dict, Any
from datetime import datetime
import re


class TimePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.description = "Get current time, date, or day of week"
        self.triggers = ["time", "date", "what day", "what's the time", "what's today"]
    
    def execute(self, user_input: str, context: Dict[str, Any]) -> str:
        """Get time/date information"""
        now = datetime.now()
        user_lower = user_input.lower()
        
        # Check what user is asking for
        if "date" in user_lower:
            return f"Today is {now.strftime('%A, %B %d, %Y')}."
        
        elif "day" in user_lower:
            return f"Today is {now.strftime('%A')}."
        
        elif "time" in user_lower:
            return f"The current time is {now.strftime('%I:%M %p')}."
        
        else:
            # Default: provide both date and time
            return f"It's {now.strftime('%I:%M %p on %A, %B %d, %Y')}."


class TimerPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.description = "Set a timer or alarm"
        self.triggers = ["timer", "set timer", "remind me", "alarm"]
        self.timers = {}
    
    def execute(self, user_input: str, context: Dict[str, Any]) -> str:
        """Handle timer requests"""
        # Extract duration
        duration = self._extract_duration(user_input)
        
        if duration:
            # In a real implementation, this would actually set a timer
            # For now, just acknowledge
            return f"I would set a timer for {duration}, but timer functionality requires a background task system. This is a demo plugin."
        else:
            return "How long should I set the timer for?"
    
    def _extract_duration(self, text: str) -> str:
        """Extract duration from text"""
        patterns = [
            r"(\d+)\s*(minute|minutes|min|mins)",
            r"(\d+)\s*(second|seconds|sec|secs)",
            r"(\d+)\s*(hour|hours|hr|hrs)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return f"{match.group(1)} {match.group(2)}"
        
        return ""
