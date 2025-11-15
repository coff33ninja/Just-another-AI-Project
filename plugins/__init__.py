"""
Plugin System for Voice Assistant

Plugins can extend the assistant's functionality with custom actions.
Each plugin should inherit from Plugin base class and implement execute().
"""

import importlib
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class Plugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.description = ""
        self.triggers = []  # Keywords that activate this plugin
    
    @abstractmethod
    def execute(self, user_input: str, context: Dict[str, Any]) -> str:
        """
        Execute the plugin's action
        
        Args:
            user_input: The user's input text
            context: Dictionary with conversation context
            
        Returns:
            Response string or None if plugin doesn't handle this input
        """
        pass
    
    def should_handle(self, user_input: str) -> bool:
        """Check if this plugin should handle the input"""
        user_lower = user_input.lower()
        return any(trigger in user_lower for trigger in self.triggers)


class PluginManager:
    """Manages loading and executing plugins"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: List[Plugin] = []
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all plugins from the plugins directory"""
        if not os.path.exists(self.plugins_dir):
            print(f"⚠ Plugins directory not found: {self.plugins_dir}")
            return
        
        # Get all Python files in plugins directory
        plugin_files = [f[:-3] for f in os.listdir(self.plugins_dir) 
                       if f.endswith('.py') and not f.startswith('_')]
        
        for plugin_name in plugin_files:
            try:
                # Import the plugin module
                module = importlib.import_module(f"{self.plugins_dir}.{plugin_name}")
                
                # Find Plugin classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, Plugin) and 
                        attr != Plugin):
                        plugin = attr()
                        self.plugins.append(plugin)
                        print(f"✓ Loaded plugin: {plugin.name}")
            
            except Exception as e:
                print(f"⚠ Failed to load plugin {plugin_name}: {e}")
    
    def process_input(self, user_input: str, context: Dict[str, Any]) -> str:
        """
        Process user input through plugins
        
        Returns:
            Plugin response or None if no plugin handles the input
        """
        for plugin in self.plugins:
            if plugin.should_handle(user_input):
                try:
                    response = plugin.execute(user_input, context)
                    if response:
                        return response
                except Exception as e:
                    print(f"⚠ Plugin {plugin.name} error: {e}")
        
        return None
    
    def get_plugin_info(self) -> List[Dict[str, str]]:
        """Get information about loaded plugins"""
        return [
            {
                "name": plugin.name,
                "description": plugin.description,
                "triggers": ", ".join(plugin.triggers)
            }
            for plugin in self.plugins
        ]
