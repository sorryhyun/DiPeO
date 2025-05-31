"""Legacy run_graph module - imports refactored execution components for backward compatibility."""

# Re-export the refactored components for backward compatibility
from .execution import DiagramExecutor

__all__ = ["DiagramExecutor"]