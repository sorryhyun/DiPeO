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
    from .handlers import simple_nodes  # noqa: F401
    
    # Import all handler modules - using v2 versions where available
    from .handlers import (  # noqa: F401
        condition_handler_v2,
        db_handler_v2,
        endpoint_handler_v2,
        job_handler_v2,
        notion_handler_v2,
        person_job_handler_v2,
    )
