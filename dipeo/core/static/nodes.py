"""Re-export generated static node types.

This module re-exports all node types from the auto-generated module.
The actual node definitions are generated from domain models to ensure
consistency across the codebase.
"""

# Re-export everything from the generated module
from dipeo.core.static.generated_nodes import (
    # Base class
    BaseExecutableNode,
    
    # Node types
    StartNode,
    EndpointNode,
    PersonJobNode,
    PersonJobNode as PersonNode,  # Alias for compatibility
    ConditionNode,
    CodeJobNode,
    ApiJobNode,
    DBNode,
    UserResponseNode,
    NotionNode,
    PersonBatchJobNode,
    HookNode,
    
    # Union type
    ExecutableNode,
    
    # Factory function
    create_executable_node
)

__all__ = [
    'BaseExecutableNode',
    'StartNode',
    'EndpointNode',
    'PersonJobNode',
    'PersonNode',  # Aliased from PersonJobNode
    'ConditionNode',
    'CodeJobNode',
    'ApiJobNode',
    'DBNode',
    'UserResponseNode',
    'NotionNode',
    'PersonBatchJobNode',
    'HookNode',
    'ExecutableNode',
    'create_executable_node'
]