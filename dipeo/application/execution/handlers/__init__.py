"""
Handler module initialization with auto-registration.

This module automatically imports all handler classes using the auto_register system,
eliminating the need for manual imports when adding new handlers.
"""

from .auto_register import auto_register_handlers, get_handler_exports

# Auto-register all handlers
registered_handlers = auto_register_handlers()

# Create a dynamic __all__ list
__all__ = get_handler_exports()

# Make handler classes available as module attributes
# This maintains backward compatibility with existing imports
for handler in registered_handlers:
    globals()[handler.__name__] = handler