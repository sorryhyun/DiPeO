"""Handler for SubDiagramNode - executes diagrams within diagrams.

This modular structure follows the pattern of condition and code_job handlers:
- __init__.py - Main handler with routing logic
- single_executor.py - Single sub-diagram execution
- batch_executor.py - Optimized parallel batch execution
- lightweight_executor.py - Lightweight execution without state persistence
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry import (
    DIAGRAM_PORT,
    MESSAGE_ROUTER,
    PREPARE_DIAGRAM_USE_CASE,
    STATE_STORE,
)
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.sub_diagram_node import NodeType, SubDiagramNode
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

from .base_executor import BaseSubDiagramExecutor
from .batch_executor import BatchSubDiagramExecutor
from .lightweight_executor import LightweightSubDiagramExecutor
from .single_executor import SingleSubDiagramExecutor

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


@register_handler
@requires_services(
    state_store=STATE_STORE,
    message_router=MESSAGE_ROUTER,
    diagram_service=DIAGRAM_PORT,
    prepare_use_case=PREPARE_DIAGRAM_USE_CASE,
)
class SubDiagramNodeHandler(TypedNodeHandler[SubDiagramNode]):
    """Handler for executing diagrams within diagrams with envelope support.

    This handler supports three execution modes:
    1. Lightweight execution (default) - Runs without state persistence
    2. Single execution - Standard sub-diagram execution with state tracking
    3. Batch execution - Process multiple items through the same sub-diagram

    Routes execution to appropriate executor based on configuration.
    Now uses envelope-based communication for clean interfaces.
    """

    NODE_TYPE = NodeType.SUB_DIAGRAM.value

    def __init__(self):
        super().__init__()
        # Executors are stateless and safe to reuse across requests
        self.lightweight_executor = LightweightSubDiagramExecutor()
        self.single_executor = SingleSubDiagramExecutor()
        self.batch_executor = BatchSubDiagramExecutor()

    @property
    def node_class(self) -> type[SubDiagramNode]:
        return SubDiagramNode

    @property
    def node_type(self) -> str:
        return NodeType.SUB_DIAGRAM.value

    @property
    def schema(self) -> type[BaseModel]:
        return SubDiagramNode

    @property
    def description(self) -> str:
        return "Execute another diagram as a node within the current diagram, supporting single and batch execution"

    def validate(self, request: ExecutionRequest[SubDiagramNode]) -> str | None:
        node = request.node

        if not node.diagram_name and not node.diagram_data:
            return "Either diagram_name or diagram_data must be specified"

        # diagram_data takes precedence when both are provided
        if node.diagram_name and node.diagram_data:
            logger.debug(
                f"Both diagram_name and diagram_data provided for node {node.id}. diagram_data will be used."
            )

        if getattr(node, "batch", False):
            batch_input_key = getattr(node, "batch_input_key", "items")
            if not batch_input_key:
                return "Batch mode enabled but batch_input_key not specified"

        return None

    async def pre_execute(self, request: ExecutionRequest[SubDiagramNode]) -> Envelope | None:
        # Configure services for executors (no caching to avoid statefulness)
        state_store = request.get_optional_service(STATE_STORE)
        message_router = request.get_optional_service(MESSAGE_ROUTER)
        diagram_service = request.get_optional_service(DIAGRAM_PORT)
        prepare_use_case = request.get_optional_service(PREPARE_DIAGRAM_USE_CASE)

        # Get event bus from registry to ensure metrics are captured for sub-diagrams
        from dipeo.application.registry import EVENT_BUS

        event_bus = request.get_optional_service(EVENT_BUS)

        self.single_executor.set_services(
            state_store=state_store,
            message_router=message_router,
            diagram_service=diagram_service,
            service_registry=request.services,
            event_bus=event_bus,
        )

        self.batch_executor.set_services(
            state_store=state_store,
            message_router=message_router,
            diagram_service=diagram_service,
            service_registry=request.services,
            event_bus=event_bus,
        )

        self.lightweight_executor.set_services(
            prepare_use_case=prepare_use_case,
            diagram_service=diagram_service,
            service_registry=request.services,
            event_bus=event_bus,
        )

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[SubDiagramNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelopes to legacy inputs for executors.

        Phase 5: Consumes tokens from incoming edges when available.
        """
        envelope_inputs = self.get_effective_inputs(request, inputs)

        # Temporary conversion layer during migration to allow existing executors to work
        legacy_inputs = {}
        for key, envelope in envelope_inputs.items():
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

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[SubDiagramNode]) -> Any:
        node = request.node

        if getattr(node, "ignoreIfSub", False) and request.metadata.get("is_sub_diagram", False):
            logger.info(
                f"Skipping sub-diagram '{node.diagram_name}' (node: {node.id}) due to ignoreIfSub=true (parent: {request.metadata.get('parent_diagram', 'unknown')})"
            )
            return EnvelopeFactory.create(
                body={
                    "skipped": True,
                    "reason": "ignoreIfSub flag is set and already in sub-diagram context",
                },
                produced_by=node.id,
                trace_id=request.execution_id or "",
                meta={
                    "diagram_name": node.diagram_name or "inline",
                    "execution_mode": "skipped",
                    "parent_diagram": request.metadata.get("parent_diagram", "unknown"),
                },
            )

        request.inputs = inputs

        if getattr(node, "batch", False):
            result = await self.batch_executor.execute(request)
        elif getattr(node, "use_standard_execution", False):
            result = await self.single_executor.execute(request)
        else:
            result = await self.lightweight_executor.execute(request)

        return result

    def _build_node_output(
        self, result: Any, request: ExecutionRequest[SubDiagramNode]
    ) -> dict[str, Any]:
        node = request.node
        is_batch = getattr(node, "batch", False)

        primary_value = result.value if hasattr(result, "value") else result

        if is_batch and isinstance(primary_value, dict):
            total_items = primary_value.get("total_items", 0)
            successful = primary_value.get("successful", 0)
            failed = primary_value.get("failed", 0)

            representations = {
                "text": f"Sub-diagram batch: {successful}/{total_items} successful",
                "object": primary_value,
                "outputs": primary_value.get("results", [])
                if isinstance(primary_value, dict)
                else [],
                "execution_stats": {
                    "nodes_executed": total_items,
                    "successful": successful,
                    "failed": failed,
                    "execution_mode": "batch",
                },
            }
        else:
            representations = {
                "text": str(primary_value)
                if not isinstance(primary_value, dict)
                else self._summarize_execution(primary_value),
                "object": primary_value,
                "outputs": self._extract_outputs(primary_value),
                "execution_stats": {
                    "nodes_executed": len(primary_value) if isinstance(primary_value, dict) else 1,
                    "execution_mode": "single"
                    if getattr(node, "use_standard_execution", False)
                    else "lightweight",
                },
            }

        return {
            "primary": primary_value,
            "representations": representations,
            "meta": {
                "diagram_name": node.diagram_name or "inline",
                "execution_mode": "batch"
                if is_batch
                else (
                    "single" if getattr(node, "use_standard_execution", False) else "lightweight"
                ),
            },
        }

    def _summarize_execution(self, result: dict) -> str:
        if not isinstance(result, dict):
            return str(result)

        node_count = len(result)
        return f"Executed {node_count} nodes in sub-diagram"

    def _extract_outputs(self, result: Any) -> dict:
        if not isinstance(result, dict):
            return {}

        outputs = {}
        for node_id, value in result.items():
            if hasattr(value, "body"):
                outputs[node_id] = value.body
            else:
                outputs[node_id] = value

        return outputs

    def serialize_output(self, result: Any, request: ExecutionRequest[SubDiagramNode]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        output = self._build_node_output(result, request)

        primary = output["primary"]
        output_envelope = EnvelopeFactory.create(
            body=primary, produced_by=node.id, trace_id=trace_id, meta={}
        )

        if "meta" in output:
            output_envelope = output_envelope.with_meta(**output["meta"])

        return output_envelope

    async def on_error(
        self, request: ExecutionRequest[SubDiagramNode], error: Exception
    ) -> Envelope | None:
        # ValueError (domain validation) is logged only in debug mode
        if isinstance(error, ValueError):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Validation error in sub-diagram: {error}")
        else:
            logger.error(f"Error executing sub-diagram: {error}")

        return EnvelopeFactory.create(
            body={"error": str(error)},
            produced_by=request.node.id,
            trace_id=request.execution_id or "",
            meta={
                "error_type": error.__class__.__name__,
                "is_error": True,
                "execution_status": "failed",
            },
        )

    def post_execute(self, request: ExecutionRequest[SubDiagramNode], output: Envelope) -> Envelope:
        """Post-execution hook to log execution details and emit tokens.

        Phase 5: Emits output as tokens to trigger downstream nodes.
        """
        if logger.isEnabledFor(logging.DEBUG):
            is_batch = getattr(request.node, "batch", False)
            if is_batch:
                batch_info = output.value if hasattr(output, "value") else {}
                total = batch_info.get("total_items", 0)
                successful = batch_info.get("successful", 0)

        self.emit_token_outputs(request, output)

        return output
