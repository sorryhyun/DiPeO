"""
Handler module initialization with auto-registration.

This module automatically imports all handler classes using the auto_register system,
eliminating the need for manual imports when adding new handlers.
"""

import logging

logger = logging.getLogger(__name__)

from .auto_register import auto_register_handlers, get_handler_exports

# Auto-register all handlers
logger.info("🔄 Auto-registering handlers...")
registered_handlers = auto_register_handlers()
logger.info(f"✅ Registered {len(registered_handlers)} handlers: {[h.__name__ for h in registered_handlers]}")

# Create a dynamic __all__ list
__all__ = get_handler_exports()

# Make handler classes available as module attributes
# This maintains backward compatibility with existing imports
for handler in registered_handlers:
    globals()[handler.__name__] = handler