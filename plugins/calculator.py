"""
Calculator Plugin - Perform mathematical calculations
"""

from plugins import Plugin
from typing import Dict, Any
import re


class CalculatorPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.description = "Perform mathematical calculations"
        self.triggers = ["calculate", "what is", "what's", "compute", "math"]
    
    def execute(self, user_input: str, context: Dict[str, Any]) -> str:
        """Perform calculation"""
        # Extract mathematical expression
        expression = self._extract_expression(user_input)
        
        if not expression:
            return None  # Let Gemini handle it
        
        try:
            # Use safe evaluation
            result = self._safe_eval(expression)
            return f"The answer is {result}."
        
        except Exception as e:
            return None  # Let Gemini handle complex math
    
    def _extract_expression(self, text: str) -> str:
        """Extract mathematical expression from text"""
        # Replace words with operators
        text = text.lower()
        text = re.sub(r'\bplus\b|\band\b', '+', text)
        text = re.sub(r'\bminus\b', '-', text)
        text = re.sub(r'\btimes\b|\bmultiplied by\b', '*', text)
        text = re.sub(r'\bdivided by\b', '/', text)
        
        # Extract pattern like "what is 5 + 3"
        patterns = [
            r"what(?:'s| is)\s+([\d\s\+\-\*/\(\)\.]+)",
            r"calculate\s+([\d\s\+\-\*/\(\)\.]+)",
            r"compute\s+([\d\s\+\-\*/\(\)\.]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                expr = match.group(1).strip()
                # Validate it's a simple math expression
                if re.match(r'^[\d\s\+\-\*/\(\)\.]+$', expr):
                    return expr
        
        return ""
    
    def _safe_eval(self, expression: str):
        """Safely evaluate mathematical expression"""
        # Only allow safe mathematical operations
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        
        # Use eval with restricted globals (safe for simple math)
        return eval(expression, {"__builtins__": {}}, {})
