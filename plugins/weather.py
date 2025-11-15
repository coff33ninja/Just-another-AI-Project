"""
Weather Plugin - Get current weather information
Requires: requests
"""

from plugins import Plugin
from typing import Dict, Any
import re


class WeatherPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.description = "Get current weather information for a location"
        self.triggers = ["weather", "temperature", "forecast", "how hot", "how cold"]
    
    def execute(self, user_input: str, context: Dict[str, Any]) -> str:
        """Get weather information"""
        try:
            import requests
        except ImportError:
            return "Weather plugin requires 'requests' library. Install with: pip install requests"
        
        # Extract location from input
        location = self._extract_location(user_input)
        
        if not location:
            return "Where would you like to know the weather for?"
        
        try:
            # Using wttr.in API (no key required)
            url = f"https://wttr.in/{location}?format=j1"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                current = data['current_condition'][0]
                
                temp_c = current['temp_C']
                temp_f = current['temp_F']
                desc = current['weatherDesc'][0]['value']
                feels_c = current['FeelsLikeC']
                humidity = current['humidity']
                
                return (f"The weather in {location} is currently {desc}. "
                       f"Temperature is {temp_c}°C ({temp_f}°F), "
                       f"feels like {feels_c}°C. "
                       f"Humidity is {humidity}%.")
            else:
                return f"Sorry, I couldn't find weather information for {location}."
        
        except Exception as e:
            return f"Sorry, I encountered an error getting the weather: {str(e)}"
    
    def _extract_location(self, text: str) -> str:
        """Extract location from user input"""
        # Common patterns
        patterns = [
            r"weather in ([\w\s]+)",
            r"weather for ([\w\s]+)",
            r"weather at ([\w\s]+)",
            r"temperature in ([\w\s]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        # Check for common location words at the end
        words = text.split()
        if len(words) >= 2:
            # Take last 1-2 words as potential location
            return " ".join(words[-2:])
        
        return ""
