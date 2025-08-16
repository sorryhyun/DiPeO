"""Standard runtime input resolver implementation.

This resolver handles the actual value resolution during diagram execution,
using a composable pipeline architecture with focused stages.
"""

from typing import Any
import asyncio
import concurrent.futures

from dipeo.core.execution.runtime_resolver import RuntimeResolver
from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.core.execution.envelope import Envelope
from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableEdgeV2,
    ExecutableNode,
    ExecutableDiagram
)

from .pipeline import InputResolutionPipeline


class StandardRuntimeResolver(RuntimeResolver):
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
    
    # ============= Stub Methods for Protocol Compliance =============
    # These methods are required by the RuntimeResolver protocol but
    # are not actually used anywhere in the codebase.
    
    def resolve_single_input(
        self,
        node: ExecutableNode,
        input_name: str,
        edge: ExecutableEdgeV2,
        context: ExecutionContext
    ) -> Any:
        """Not used - stub for protocol compliance."""
        raise NotImplementedError("Use resolve_node_inputs instead")
    
    def extract_output_value(
        self,
        output: Envelope,
        output_name: str = "default"
    ) -> Any:
        """Not used - stub for protocol compliance."""
        if isinstance(output, Envelope):
            return output.body if output_name == "default" else None
        return None
    
    def apply_transformation(
        self,
        value: Any,
        transformation_rules: dict[str, Any],
        source_context: dict[str, Any] | None = None
    ) -> Any:
        """Not used - stub for protocol compliance."""
        return value  # No transformation
    
    def register_transformation(
        self,
        name: str,
        rule: Any
    ) -> None:
        """Not used - stub for protocol compliance."""
        pass  # No-op
    
    def resolve_default_value(
        self,
        node: ExecutableNode,
        input_name: str,
        input_type: str | None = None
    ) -> Any:
        """Not used - stub for protocol compliance."""
        return None
    
    def resolve_conditional_input(
        self,
        node: ExecutableNode,
        edges: list[ExecutableEdgeV2],
        context: ExecutionContext,
        condition_key: str = "is_conditional"
    ) -> dict[str, Any]:
        """Not used - stub for protocol compliance."""
        return {}
    
    def validate_resolved_inputs(
        self,
        node: ExecutableNode,
        inputs: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Not used - stub for protocol compliance."""
        return True, []
    
    def get_transformation_chain(
        self,
        source_type: str,
        target_type: str
    ) -> list[Any] | None:
        """Not used - stub for protocol compliance."""
        return None