"""DiPeO Backend API Server.

This package provides the API service for DiPeO:
- FastAPI server with GraphQL endpoint
- MCP (Model Context Protocol) integration
- Webhook endpoints
- Execution monitoring and management API

The server is a consumer of the dipeo core library, providing
an HTTP/GraphQL interface for diagram operations, execution
management, and integration with external services.
"""

import sys
from types import ModuleType

__version__ = "1.0.0"

# Backward compatibility: Make this module accessible as 'dipeo_server'
# to support legacy imports (e.g., 'from dipeo_server import ...')
# This allows a gradual migration from the old module structure
_this_module = sys.modules[__name__]
sys.modules["dipeo_server"] = _this_module

# Also create a dipeo_server namespace that mirrors this module's structure
# This handles imports like 'from dipeo_server.api import ...'
class _CompatModule(ModuleType):
    """Compatibility module that redirects to the new server module."""

    def __getattr__(self, name):
        # Import the actual module from server.*
        try:
            actual_module = __import__(f"server.{name}", fromlist=[name])
            return actual_module
        except ImportError:
            raise AttributeError(f"module 'dipeo_server' has no attribute '{name}'")

# Set up the compatibility module
_compat_module = _CompatModule("dipeo_server")
_compat_module.__path__ = _this_module.__path__ if hasattr(_this_module, '__path__') else []
sys.modules["dipeo_server"] = _compat_module
