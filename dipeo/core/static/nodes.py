"""Re-export generated static node types.

This module re-exports all node types from the auto-generated module.
The actual node definitions are generated from domain models to ensure
consistency across the codebase.
"""

# Re-export everything from the generated module
from dipeo.core.static.generated_nodes import (
    ApiJobNode,
    # Base class
    BaseExecutableNode,
    CodeJobNode,
    ConditionNode,
    DBNode,
    EndpointNode,
    # Union type
    ExecutableNode,
    HookNode,
    NotionNode,
    PersonBatchJobNode,
    PersonJobNode,
    # Node types
    StartNode,
    UserResponseNode,
    # Factory function
    create_executable_node,
)
from dipeo.core.static.generated_nodes import PersonJobNode as PersonNode  # Alias for compatibility

__all__ = [
    'ApiJobNode',
    'BaseExecutableNode',
    'CodeJobNode',
    'ConditionNode',
    'DBNode',
    'EndpointNode',
    'ExecutableNode',
    'HookNode',
    'NotionNode',
    'PersonBatchJobNode',
    'PersonJobNode',
    'PersonNode',  # Aliased from PersonJobNode
    'StartNode',
    'UserResponseNode',
    'create_executable_node'
]