"""Handler for SubDiagramNode - executes diagrams within diagrams.

This modular structure follows the pattern of condition and code_job handlers:
- __init__.py - Main handler with routing logic
- single_executor.py - Single sub-diagram execution  
- batch_executor.py - Optimized parallel batch execution
- lightweight_executor.py - Lightweight execution without state persistence
"""

import logging
from typing import TYPE_CHECKING, Optional, Any

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.generated_nodes import NodeType, SubDiagramNode
from dipeo.diagram_generated.models.sub_diagram_model import SubDiagramNodeData

from .base_executor import BaseSubDiagramExecutor
from .batch_executor import BatchSubDiagramExecutor
from .lightweight_executor import LightweightSubDiagramExecutor
from .single_executor import SingleSubDiagramExecutor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_handler
class SubDiagramNodeHandler(TypedNodeHandler[SubDiagramNode]):
    """Handler for executing diagrams within diagrams with envelope support.
    
    This handler supports three execution modes:
    1. Lightweight execution (default) - Runs without state persistence
    2. Single execution - Standard sub-diagram execution with state tracking
    3. Batch execution - Process multiple items through the same sub-diagram
    
    Routes execution to appropriate executor based on configuration.
    Now uses envelope-based communication for clean interfaces.
    """
    
    
    def __init__(self):
        """Initialize executors."""
        super().__init__()
        # Initialize executors
        self.lightweight_executor = LightweightSubDiagramExecutor()
        self.single_executor = SingleSubDiagramExecutor()
        self.batch_executor = BatchSubDiagramExecutor()
        
        # Services configured flag
        self._services_configured = False
    
    @property
    def node_class(self) -> type[SubDiagramNode]:
        return SubDiagramNode
    
    @property
    def node_type(self) -> str:
        return NodeType.SUB_DIAGRAM.value

    @property
    def schema(self) -> type[BaseModel]:
        return SubDiagramNodeData

    @property
    def requires_services(self) -> list[str]:
        return [
            "state_store",
            "message_router",
            "diagram_service_new",
            "prepare_diagram_use_case"
        ]

    @property
    def description(self) -> str:
        return "Execute another diagram as a node within the current diagram, supporting single and batch execution"
    
    def validate(self, request: ExecutionRequest[SubDiagramNode]) -> str | None:
        """Validate the execution request."""
        node = request.node
        
        # Validate that either diagram_name or diagram_data is provided
        if not node.diagram_name and not node.diagram_data:
            return "Either diagram_name or diagram_data must be specified"
        
        # If both are provided, warn but continue (diagram_data takes precedence)
        if node.diagram_name and node.diagram_data:
            logger.debug(f"Both diagram_name and diagram_data provided for node {node.id}. diagram_data will be used.")
        
        # Validate batch configuration
        if getattr(node, 'batch', False):
            batch_input_key = getattr(node, 'batch_input_key', 'items')
            if not batch_input_key:
                return "Batch mode enabled but batch_input_key not specified"
        
        return None
    
    async def pre_execute(self, request: ExecutionRequest[SubDiagramNode]) -> Envelope | None:
        """Pre-execution hook to configure services and validate execution context."""
        # Configure services for executors on first execution
        if not self._services_configured:
            from dipeo.application.registry import (
                DIAGRAM_SERVICE,
                MESSAGE_ROUTER,
                PREPARE_DIAGRAM_USE_CASE,
                STATE_STORE,
            )
            
            state_store = request.services.resolve(STATE_STORE)
            message_router = request.services.resolve(MESSAGE_ROUTER)
            diagram_service = request.services.resolve(DIAGRAM_SERVICE)
            prepare_use_case = request.services.resolve(PREPARE_DIAGRAM_USE_CASE)
            
            # Validate required services
            if not all([state_store, message_router, diagram_service]):
                return EnvelopeFactory.error(
                    "Required services not available for sub-diagram execution",
                    error_type="ValueError",
                    produced_by=request.node.id,
                    trace_id=request.execution_id or ""
                )
            
            # Set services on executors
            self.single_executor.set_services(
                state_store=state_store,
                message_router=message_router,
                diagram_service=diagram_service
            )
            
            self.batch_executor.set_services(
                state_store=state_store,
                message_router=message_router,
                diagram_service=diagram_service
            )
            
            self.lightweight_executor.set_services(
                prepare_use_case=prepare_use_case,
                diagram_service=diagram_service
            )
            
            self._services_configured = True
        
        # Return None to proceed with normal execution
        return None
    
    async def prepare_inputs(
        self,
        request: ExecutionRequest[SubDiagramNode],
        inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelopes to legacy inputs for executors."""
        # Convert envelopes to legacy inputs for executors (temporary during migration)
        # This allows existing executors to work without modification
        legacy_inputs = {}
        for key, envelope in inputs.items():
            if envelope.content_type == "raw_text":
                legacy_inputs[key] = envelope.as_text()
            elif envelope.content_type == "object":
                legacy_inputs[key] = envelope.as_json()
            elif envelope.content_type == "binary":
                legacy_inputs[key] = envelope.as_bytes()
            elif envelope.content_type == "conversation_state":
                legacy_inputs[key] = envelope.as_conversation()
            else:
                legacy_inputs[key] = envelope.body
        return legacy_inputs
    
    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[SubDiagramNode]
    ) -> Any:
        """Route execution to appropriate executor based on configuration."""
        node = request.node
        
        # Update request inputs for executors
        request.inputs = inputs
        
        # Route to appropriate executor
        if getattr(node, 'batch', False):
            result = await self.batch_executor.execute(request)
        elif getattr(node, 'use_standard_execution', False):
            result = await self.single_executor.execute(request)
        else:
            result = await self.lightweight_executor.execute(request)
        
        return result
    
    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[SubDiagramNode]
    ) -> Envelope:
        """Convert executor result to envelope."""
        node = request.node
        trace_id = request.execution_id or ""
        
        # Convert result to envelope
        if hasattr(result, 'value'):
            # Check if it's a dict (typical for batch or complex results)
            if isinstance(result.value, dict):
                output_envelope = EnvelopeFactory.json(
                    result.value,
                    produced_by=node.id,
                    trace_id=trace_id
                ).with_meta(
                    diagram_name=node.diagram_name or "inline",
                    execution_mode="batch" if getattr(node, 'batch', False) else "single"
                )
            else:
                # Text output
                output_envelope = EnvelopeFactory.text(
                    str(result.value),
                    produced_by=node.id,
                    trace_id=trace_id
                ).with_meta(
                    diagram_name=node.diagram_name or "inline"
                )
        else:
            # Fallback for unexpected result format
            output_envelope = EnvelopeFactory.text(
                str(result),
                produced_by=node.id,
                trace_id=trace_id
            )
        
        return output_envelope
    
    async def on_error(
        self,
        request: ExecutionRequest[SubDiagramNode],
        error: Exception
    ) -> Envelope | None:
        """Handle errors gracefully."""
        # For ValueError (domain validation), only log in debug mode
        if isinstance(error, ValueError):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Validation error in sub-diagram: {error}")
        else:
            # For other errors, log them
            logger.error(f"Error executing sub-diagram: {error}")
        
        return EnvelopeFactory.error(
            str(error),
            error_type=error.__class__.__name__,
            produced_by=request.node.id,
            trace_id=request.execution_id or ""
        )
    
    def post_execute(
        self,
        request: ExecutionRequest[SubDiagramNode],
        output: Envelope
    ) -> Envelope:
        """Post-execution hook to log execution details."""
        # Log execution details in debug mode
        if logger.isEnabledFor(logging.DEBUG):
            is_batch = getattr(request.node, 'batch', False)
            if is_batch:
                batch_info = output.value if hasattr(output, 'value') else {}
                total = batch_info.get('total_items', 0)
                successful = batch_info.get('successful', 0)

        return output