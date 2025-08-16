"""Simplified runtime resolver protocol focused on actual usage."""

from typing import Any, Protocol

from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2, ExecutableNode
from dipeo.core.execution.execution_context import ExecutionContext


class RuntimeResolverV2(Protocol):
    """Minimal runtime resolver protocol.
    
    This simplified protocol focuses on the single essential method
    actually used in practice: resolve_node_inputs.
    
    All other resolution logic is handled internally by implementations.
    """
    
    def resolve_node_inputs(
        self,
        node: ExecutableNode,
        incoming_edges: list[ExecutableEdgeV2],
        context: ExecutionContext
    ) -> dict[str, Any]:
        """
        Resolve all inputs for a node at runtime.
        
        This is the only method required by the protocol.
        All transformation, filtering, and default value logic
        is handled internally by the implementation.
        
        Args:
            node: The node to resolve inputs for
            incoming_edges: Edges targeting this node
            context: Current execution context with node states
            
        Returns:
            Dictionary of resolved input values by handle name
            
        Raises:
            ResolutionError: If inputs cannot be resolved
        """
        ...