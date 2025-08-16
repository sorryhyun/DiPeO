"""Main pipeline orchestrator for input resolution."""

import logging
from typing import Any

from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.core.execution.envelope import Envelope
from dipeo.core.execution.resolution_error import ResolutionError
from dipeo.domain.diagram.models.executable_diagram import (
    ExecutableNode,
    ExecutableDiagram
)

from .base import PipelineContext
from .incoming_edges import IncomingEdgesStage
from .filter import FilterStage
from .transform import TransformStage
from .defaults import DefaultsStage

log = logging.getLogger(__name__)


class InputResolutionPipeline:
    """Orchestrates the input resolution pipeline.
    
    This pipeline breaks down the complex input resolution process
    into focused, composable stages:
    
    1. IncomingEdges: Collect edges and retrieve values
    2. Filter: Apply strategy-based filtering
    3. Transform: Apply data transformations
    4. Defaults: Apply default values
    
    Each stage is ~50-100 lines focused on a single responsibility,
    replacing the monolithic 520-line StandardRuntimeResolver.
    """
    
    def __init__(self):
        """Initialize the pipeline with default stages."""
        self.stages = [
            IncomingEdgesStage(),
            FilterStage(),
            TransformStage(),
            DefaultsStage(),
        ]
    
    async def resolve(
        self,
        node: ExecutableNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram
    ) -> dict[str, Any]:
        """Resolve inputs for a node through the pipeline.
        
        Args:
            node: The node to resolve inputs for
            context: Execution context with node states
            diagram: The executable diagram
            
        Returns:
            Dictionary of resolved inputs
        """
        # Create pipeline context
        ctx = PipelineContext(
            node=node,
            context=context,
            diagram=diagram
        )
        
        # Run through pipeline stages
        try:
            for stage in self.stages:
                ctx = await stage.process(ctx)
        except ResolutionError as e:
            # Add node context if not already present
            if not e.node_id:
                e.node_id = str(node.id)
            log.error(f"Resolution error for node {node.id}: {e}")
            raise
        except Exception as e:
            # Wrap unexpected errors in ResolutionError
            log.error(f"Unexpected error in resolution pipeline for node {node.id}: {e}")
            from dipeo.core.execution.resolution_error import InputResolutionError
            raise InputResolutionError(
                f"Failed to resolve inputs: {str(e)}",
                node_id=str(node.id)
            ) from e
        
        # Check for validation errors (warnings, not failures)
        if hasattr(ctx, 'validation_errors') and ctx.validation_errors:
            # Log warnings but don't fail - let handler decide
            for error in ctx.validation_errors:
                log.warning(f"Input validation warning for {node.id}: {error}")
        
        return ctx.final_inputs
    
    async def resolve_as_envelopes(
        self,
        node: ExecutableNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram
    ) -> dict[str, Envelope]:
        """Resolve inputs as envelopes (for envelope-aware handlers).
        
        This is used by handlers that need envelope metadata in addition
        to the raw values.
        """
        # For now, delegate to regular resolve
        # In future, we could have envelope-specific pipeline stages
        inputs = await self.resolve(node, context, diagram)
        
        # Convert to envelopes if needed
        envelopes = {}
        for key, value in inputs.items():
            if isinstance(value, Envelope):
                envelopes[key] = value
            else:
                # Create envelope from value
                from dipeo.core.execution.envelope import EnvelopeFactory
                from uuid import uuid4
                
                trace_id = getattr(context, 'execution_id', str(uuid4()))
                
                if isinstance(value, str):
                    envelope = EnvelopeFactory.text(
                        value,
                        produced_by=str(node.id),
                        trace_id=trace_id
                    )
                elif isinstance(value, (dict, list)):
                    envelope = EnvelopeFactory.json(
                        value,
                        produced_by=str(node.id),
                        trace_id=trace_id
                    )
                else:
                    envelope = EnvelopeFactory.text(
                        str(value),
                        produced_by=str(node.id),
                        trace_id=trace_id
                    )
                
                envelopes[key] = envelope
        
        return envelopes
    
    def add_stage(self, stage, index: int | None = None) -> None:
        """Add a custom stage to the pipeline.
        
        Args:
            stage: The stage to add
            index: Position to insert at (None = end)
        """
        if index is None:
            self.stages.append(stage)
        else:
            self.stages.insert(index, stage)
    
    def remove_stage(self, stage_name: str) -> bool:
        """Remove a stage by name.
        
        Args:
            stage_name: Name of the stage class
            
        Returns:
            True if removed, False if not found
        """
        for i, stage in enumerate(self.stages):
            if stage.name == stage_name:
                del self.stages[i]
                return True
        return False
    
    def replace_stage(self, stage_name: str, new_stage) -> bool:
        """Replace a stage with a new implementation.
        
        Args:
            stage_name: Name of the stage to replace
            new_stage: New stage instance
            
        Returns:
            True if replaced, False if not found
        """
        for i, stage in enumerate(self.stages):
            if stage.name == stage_name:
                self.stages[i] = new_stage
                return True
        return False