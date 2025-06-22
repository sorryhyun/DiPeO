"""Registry for creating and configuring the unified executor."""

from typing import Any, Dict, Optional

from .decorators import get_registered_nodes
from .unified_executor import UnifiedExecutor


def create_executor(services: Optional[Dict[str, Any]] = None) -> UnifiedExecutor:
    """Create and configure the unified executor with all node types."""
    executor = UnifiedExecutor(service_provider=services)

    # Import all handler modules to trigger decorator registration
    # This ensures all @node decorators are executed
    _import_all_handlers()

    # Register all nodes that were decorated with @node
    for node_def in get_registered_nodes():
        executor.register(node_def)

    return executor


def _import_all_handlers():
    """Import all handler modules to trigger decorator registration."""
    # Import simple nodes from parent directory
    from . import simple_nodes  # noqa: F401
    
    # Import all handler modules - using v2 versions where available
    from .handlers import (  # noqa: F401
        condition_handler,
        db_handler,
        endpoint_handler,
        job_handler,
        notion_handler,
        person_job_handler,
    )
