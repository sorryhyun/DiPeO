"""Decorator-based node registration system."""

from typing import Type, Callable, List, Optional
from functools import wraps
import inspect
import logging

from .types import RuntimeNodeDefinition as NodeDefinition
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
    
    Can be used with both functions and classes:
    
    Function usage:
        @node(
            node_type="person_job",
            schema=PersonJobProps,
            description="Execute LLM task with person context and memory",
            requires_services=["llm_service"]
        )
        async def person_job_handler(props, context, inputs, services):
            # Handler implementation
            pass
    
    Class usage:
        @node(
            node_type="job",
            schema=JobNodeProps,
            description="Execute code snippets"
        )
        class JobHandler(BaseNodeHandler):
            async def _execute_core(self, props, context, inputs, services):
                # Handler implementation
                pass
    """
    def decorator(handler_or_class: Callable) -> Callable:
        # Check if we're decorating a class or a function
        if inspect.isclass(handler_or_class):
            # Class-based handler
            # Check if it has BaseNodeHandler in its MRO
            from .base import BaseNodeHandler
            if not issubclass(handler_or_class, BaseNodeHandler):
                raise ValueError(
                    f"Class {handler_or_class.__name__} must inherit from BaseNodeHandler"
                )
            
            # Instantiate the class with the decorator parameters
            instance = handler_or_class(
                node_type=node_type,
                schema=schema,
                description=description,
                requires_services=requires_services
            )
            
            # The instance itself is callable via __call__
            actual_handler = instance
            
        else:
            # Function-based handler
            handler = handler_or_class
            
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
        
        # Add metadata to the original handler/class
        handler_or_class._node_type = node_type
        handler_or_class._node_schema = schema
        handler_or_class._node_description = description
        handler_or_class._node_requires = requires_services or []
        
        return handler_or_class
    
    return decorator


def get_registered_nodes() -> List[NodeDefinition]:
    """Get all nodes registered via decorators."""
    return _node_registry.copy()


