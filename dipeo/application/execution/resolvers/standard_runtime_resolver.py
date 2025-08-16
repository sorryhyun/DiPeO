"""Standard runtime input resolver implementation.

This resolver handles the actual value resolution during diagram execution,
using a composable pipeline architecture with focused stages.
"""

from typing import Any
import asyncio
import concurrent.futures

from dipeo.core.execution.runtime_resolver_v2 import RuntimeResolverV2
from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.core.execution.envelope import Envelope
from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableEdgeV2,
    ExecutableNode,
    ExecutableDiagram
)

from .pipeline import InputResolutionPipeline


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
        self.pipeline = InputResolutionPipeline()
    
    def resolve_node_inputs(
        self,
        node: ExecutableNode,
        incoming_edges: list[ExecutableEdgeV2],
        context: ExecutionContext
    ) -> dict[str, Any]:
        """Resolve all inputs for a node using the pipeline.
        
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
        
        # Use asyncio to run the async pipeline
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're already in an async context
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self.pipeline.resolve(node, context, diagram)
                )
                return future.result()
        else:
            # We can run directly
            return loop.run_until_complete(
                self.pipeline.resolve(node, context, diagram)
            )
    
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
        return await self.pipeline.resolve_as_envelopes(node, context, diagram)