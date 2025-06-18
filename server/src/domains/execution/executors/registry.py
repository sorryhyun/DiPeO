"""Registry for creating and configuring the unified executor."""

from .unified_executor import UnifiedExecutor
from .decorators import get_registered_nodes


def create_executor() -> UnifiedExecutor:
    """Create and configure the unified executor with all node types."""
    executor = UnifiedExecutor()
    
    # Import all handler modules to trigger decorator registration
    # This ensures all @node decorators are executed
    _import_all_handlers()
    
    # Register all nodes that were decorated with @node
    for node_def in get_registered_nodes():
        executor.register(node_def)
    
    return executor


def _import_all_handlers():
    """Import all handler modules to trigger decorator registration."""
    # Import simple nodes (start, user_response)
    from . import simple_nodes
    
    # Import all handler modules
    from .handlers import (
        person_job_handler,
        condition_handler,
        endpoint_handler,
        job_handler,
        db_handler,
        notion_handler
    )