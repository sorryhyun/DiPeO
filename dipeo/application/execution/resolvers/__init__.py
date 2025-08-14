"""Runtime resolvers for execution.

This package contains implementations of runtime resolvers that handle
input resolution during diagram execution.
"""

from .standard_runtime_resolver import StandardRuntimeResolver

# Global instance for the default resolver
_default_resolver = None


def get_resolver() -> StandardRuntimeResolver:
    """Get the default resolver instance.
    
    Returns a singleton instance of the StandardRuntimeResolver.
    """
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = StandardRuntimeResolver()
    return _default_resolver


__all__ = ["StandardRuntimeResolver", "get_resolver"]