"""Auto-registration system for node handlers.

This module automatically discovers and imports all handler modules in the handlers directory,
eliminating the need for manual imports in __init__.py.
"""

import importlib
import inspect
import os
from pathlib import Path
import sys
from typing import List, Type

from dipeo.application.execution.handler_base import TypedNodeHandler


def auto_register_handlers() -> List[Type[TypedNodeHandler]]:
    """
    Automatically discover and register all handler classes in the handlers directory.
    
    Returns:
        List of registered handler classes for export in __all__.
    """
    handlers_dir = Path(__file__).parent
    registered_handlers = []
    
    # Find all Python files and directories in the handlers directory
    for item_path in handlers_dir.iterdir():
        # Skip special files and non-Python files
        if item_path.name.startswith("_") or item_path.name == "auto_register.py":
            continue
        
        module_name = None
        
        # Handle regular .py files
        if item_path.is_file() and item_path.suffix == ".py":
            module_name = item_path.stem
        
        # Handle directories with __init__.py (handler packages)
        elif item_path.is_dir() and (item_path / "__init__.py").exists():
            module_name = item_path.name
        
        if module_name:
            try:
                # Import the module dynamically
                module = importlib.import_module(f".{module_name}", package="dipeo.application.execution.handlers")
                
                # Find all handler classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, TypedNodeHandler) and 
                        obj.__module__.startswith("dipeo.application.execution.handlers")):
                        # The @register_handler decorator will be called automatically
                        # when the module is imported
                        registered_handlers.append(obj)
                        
            except Exception as e:
                print(f"Warning: Failed to import handler module {module_name}: {e}")
            
    return registered_handlers


def get_handler_exports() -> List[str]:
    """
    Get list of handler class names for __all__ export.
    
    Returns:
        List of handler class names.
    """
    handlers = auto_register_handlers()
    return [handler.__name__ for handler in handlers]