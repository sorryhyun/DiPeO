"""Standard runtime input resolver implementation.

This resolver handles the actual value resolution during diagram execution,
using a composable pipeline architecture with focused stages.
"""

from typing import Any

from .runtime_resolver_protocol import RuntimeResolverV2
from dipeo.domain.execution.execution_context import ExecutionContext
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableEdgeV2,
    ExecutableNode,
    ExecutableDiagram
)

from dipeo.domain.execution.resolution import resolve_inputs


class StandardRuntimeResolver(RuntimeResolverV2):
    """Standard implementation of runtime input resolution.
    
    Delegates to a composable pipeline that splits concerns into focused stages:
    1. IncomingEdges - Edge collection (~50 lines)
    2. Filter - Dependency state filtering (~85 lines)
    3. SpecialInputs - Node-specific handling (~75 lines)
    4. Transform - Data transformations (~100 lines)
    5. Defaults - Default value application (~95 lines)
    """
    
    def __init__(self):
        # No longer need pipeline - using domain resolution directly
        pass
    
    def resolve_node_inputs(
        self,
        node: ExecutableNode,
        incoming_edges: list[ExecutableEdgeV2],
        context: ExecutionContext
    ) -> dict[str, Any]:
        """Resolve all inputs for a node using domain resolution.
        
        Args:
            node: The node to resolve inputs for
            incoming_edges: Edges targeting this node
            context: Execution context with node states
            
        Returns:
            Dictionary of resolved inputs
        """
        # Create a minimal diagram with just the edges we need
        diagram = ExecutableDiagram(
            id="temp",
            nodes=[node],
            edges=incoming_edges,
            metadata={}
        )
        
        # Use domain resolution directly (it's synchronous)
        envelopes = resolve_inputs(node, diagram, context)
        
        # Extract raw values from envelopes for backward compatibility
        return {key: env.body for key, env in envelopes.items()}
    
    async def resolve_as_envelopes(
        self,
        node: ExecutableNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram
    ) -> dict[str, Envelope]:
        """Resolve all inputs as envelopes.
        
        Used by handlers that need envelope metadata in addition to raw values.
        
        Args:
            node: The node to resolve inputs for
            context: Execution context
            diagram: The executable diagram
            
        Returns:
            Dictionary of input envelopes
        """
        # Use domain resolution directly (it's synchronous but we wrap for async interface)
        return resolve_inputs(node, diagram, context)