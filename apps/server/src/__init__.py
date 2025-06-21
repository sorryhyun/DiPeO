"""Compatibility shim for old import paths.

This module provides backward compatibility for imports using the old src.* paths.
These imports are DEPRECATED and will be removed in a future release.
Please update your imports to use dipeo_server.* instead.
"""

import warnings
import sys
from typing import Any


class DeprecatedModule:
    """A module wrapper that issues deprecation warnings."""
    
    def __init__(self, old_path: str, new_path: str, module: Any):
        self._old_path = old_path
        self._new_path = new_path
        self._module = module
    
    def __getattr__(self, name: str) -> Any:
        warnings.warn(
            f"Import from '{self._old_path}' is deprecated. "
            f"Please use '{self._new_path}' instead.",
            DeprecationWarning,
            stacklevel=3
        )
        return getattr(self._module, name)


# Import new modules
try:
    import dipeo_server.core as core_module
    import dipeo_server.domains as domains_module
    
    # Set up compatibility aliases
    sys.modules['src.common'] = DeprecatedModule('src.common', 'dipeo_server.core', core_module)
    sys.modules['src.domains'] = DeprecatedModule('src.domains', 'dipeo_server.domains', domains_module)
    
    # Also set up specific domain modules
    for domain in ['diagram', 'execution', 'integrations', 'llm', 'person']:
        if hasattr(domains_module, domain):
            old_path = f'src.domains.{domain}'
            new_path = f'dipeo_server.domains.{domain}'
            module = getattr(domains_module, domain)
            sys.modules[old_path] = DeprecatedModule(old_path, new_path, module)
    
except ImportError:
    # If new modules don't exist yet, fall back to old imports
    pass