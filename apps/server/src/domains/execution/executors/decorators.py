"""Decorator-based node registration system."""

from typing import Type, Callable, List, Dict, Any, Optional
from functools import wraps
import inspect
import logging

from .types import NodeDefinition, ExecutionContext
from .schemas.base import BaseNodeProps

logger = logging.getLogger(__name__)

# Global registry for decorated nodes
_node_registry: List[NodeDefinition] = []


def node(
    node_type: str,
    *,
    schema: Type[BaseNodeProps],
    description: str,
    requires_services: Optional[List[str]] = None
) -> Callable:
    """
    Decorator for registering node handlers.
    
    Usage:
        @node(
            node_type="person_job",
            schema=PersonJobProps,
            description="Execute LLM task with person context and memory",
            requires_services=["llm_service"]
        )
        async def person_job_handler(props, context, inputs):
            # Handler implementation
            pass
    """
    def decorator(handler: Callable) -> Callable:
        # Validate handler signature
        sig = inspect.signature(handler)
        params = list(sig.parameters.keys())
        
        # Accept both old (3 params) and new (4 params) signatures for backward compatibility
        if len(params) not in [3, 4]:
            raise ValueError(
                f"Node handler {handler.__name__} must accept 3 or 4 parameters: "
                f"(props, context, inputs) or (props, context, inputs, services). Got: {params}"
            )
        
        # Create wrapper to handle both signatures
        if len(params) == 3:
            # Old signature without services - wrap it to accept services
            @wraps(handler)
            async def wrapped_handler(props, context, inputs, services):
                # For backward compatibility, inject services into context
                # if they were expected there
                for service_name, service in services.items():
                    if not hasattr(context, service_name):
                        setattr(context, service_name, service)
                return await handler(props, context, inputs)
            actual_handler = wrapped_handler
        else:
            # New signature with services
            actual_handler = handler
        
        # Create node definition
        node_def = NodeDefinition(
            type=node_type,
            schema=schema,
            handler=actual_handler,
            requires_services=requires_services or [],
            description=description
        )
        
        # Register in global registry
        _node_registry.append(node_def)
        logger.info(f"Registered node via decorator: {node_type}")
        
        # Add metadata to the handler
        handler._node_type = node_type
        handler._node_schema = schema
        handler._node_description = description
        handler._node_requires = requires_services or []
        
        return handler
    
    return decorator


def get_registered_nodes() -> List[NodeDefinition]:
    """Get all nodes registered via decorators."""
    return _node_registry.copy()


def clear_registry() -> None:
    """Clear the node registry (useful for testing)."""
    global _node_registry
    _node_registry.clear()


def combine_handler_schema(schema_class: Type[BaseNodeProps], handler_func: Callable) -> Type:
    """
    Create a combined class that includes both schema and handler.
    This allows for cleaner organization where related code stays together.
    """
    # Check handler signature
    sig = inspect.signature(handler_func)
    params_count = len(sig.parameters)
    
    class CombinedNode(schema_class):
        @classmethod
        async def execute(cls, props: schema_class, context: ExecutionContext, inputs: Dict[str, Any], services: Dict[str, Any] = None) -> Any:
            if params_count == 3:
                # Old signature
                return await handler_func(props, context, inputs)
            else:
                # New signature
                return await handler_func(props, context, inputs, services or {})
    
    CombinedNode.__name__ = f"{schema_class.__name__}Handler"
    return CombinedNode