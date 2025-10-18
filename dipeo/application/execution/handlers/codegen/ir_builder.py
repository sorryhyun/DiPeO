"""Handler for IR builder nodes."""

from typing import Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry.keys import IR_BUILDER_REGISTRY, IR_CACHE
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.ir_builder_node import IrBuilderNode, NodeType
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

logger = get_module_logger(__name__)


@register_handler
@requires_services(
    ir_cache=IR_CACHE,
    ir_builder_registry=IR_BUILDER_REGISTRY,
)
class IrBuilderNodeHandler(TypedNodeHandler[IrBuilderNode]):
    """Handler for IR builder nodes.

    Manages IR building operations through the IR builder registry,
    with support for caching and validation.
    """

    NODE_TYPE = NodeType.IR_BUILDER

    def __init__(self):
        super().__init__()

    @property
    def node_class(self) -> type[IrBuilderNode]:
        return IrBuilderNode

    @property
    def node_type(self) -> str:
        return NodeType.IR_BUILDER.value

    @property
    def schema(self) -> type[BaseModel]:
        return IrBuilderNode

    @property
    def description(self) -> str:
        return "Builds intermediate representation (IR) from source data"

    def validate(self, request: ExecutionRequest[IrBuilderNode]) -> str | None:
        """Static validation of node configuration."""
        node = request.node

        if not node.builder_type:
            return "builder_type is required"

        if node.output_format and node.output_format not in ["json", "yaml", "raw"]:
            return f"Invalid output_format: {node.output_format}. Must be 'json', 'yaml', or 'raw'"

        return None

    async def pre_execute(self, request: ExecutionRequest[IrBuilderNode]) -> Envelope | None:
        """Runtime validation and setup."""
        node = request.node

        try:
            ir_builder_registry = request.get_required_service(IR_BUILDER_REGISTRY)
            available_builders = ir_builder_registry.list_builders()

            if node.builder_type not in available_builders:
                error_msg = f"Unknown builder type: {node.builder_type}. Available: {', '.join(available_builders)}"
                logger.error(error_msg)
                return EnvelopeFactory.create(
                    body={"error": error_msg, "type": "ValidationError"},
                    produced_by=str(node.id),
                    trace_id=request.execution_id or "",
                )

            current_builder = ir_builder_registry.get_builder(node.builder_type)
            request.set_handler_state("current_builder", current_builder)
        except Exception as e:
            logger.error(f"Failed to initialize IR builder: {e}")
            return EnvelopeFactory.create(
                body={
                    "error": f"Failed to initialize IR builder: {e}",
                    "type": "RuntimeError",
                },
                produced_by=str(node.id),
                trace_id=request.execution_id or "",
            )

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[IrBuilderNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to source data for IR building."""
        if "default" in inputs:
            envelope = inputs["default"]
            if hasattr(envelope, "body"):
                return envelope.body
            elif hasattr(envelope, "data"):
                return envelope.data
            else:
                return inputs.get("default", {})

        return {}

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[IrBuilderNode]) -> Any:
        """Execute IR building."""
        node = request.node
        current_builder = request.get_handler_state("current_builder")

        current_cache_key = current_builder.get_cache_key(inputs)
        request.set_handler_state("current_cache_key", current_cache_key)

        if node.cache_enabled:
            cached = await self._ir_cache.get(current_cache_key)
            if cached:
                return cached

        try:
            ir_data = await current_builder.build_ir(inputs)

            request.set_handler_state("current_ir_data", ir_data)

            if node.validate_output:
                if not current_builder.validate_ir(ir_data):
                    raise ValueError(f"IR validation failed for {node.builder_type}")

            if node.cache_enabled:
                await self._ir_cache.set(current_cache_key, ir_data)

            if node.output_format == "json" or node.output_format == "yaml":
                if hasattr(ir_data, "data") and hasattr(ir_data, "metadata"):
                    result = ir_data.data.copy() if isinstance(ir_data.data, dict) else ir_data.data
                    if isinstance(result, dict) and "metadata" not in result:
                        if hasattr(ir_data.metadata, "dict"):
                            result["metadata"] = ir_data.metadata.dict()
                        else:
                            result["metadata"] = ir_data.metadata
                    return result
                elif hasattr(ir_data, "dict"):
                    ir_dict = ir_data.dict()
                    if "data" in ir_dict and "metadata" in ir_dict:
                        result = (
                            ir_dict["data"].copy()
                            if isinstance(ir_dict["data"], dict)
                            else ir_dict["data"]
                        )
                        if isinstance(result, dict):
                            result["metadata"] = ir_dict["metadata"]
                        return result
                    return ir_dict.get("data", ir_dict)
                else:
                    return ir_data
            else:
                return ir_data

        except Exception as e:
            logger.error(f"Failed to build IR: {e}")
            raise

    def serialize_output(self, result: Any, request: ExecutionRequest[IrBuilderNode]) -> Envelope:
        """Serialize IR data to envelope."""
        node = request.node

        envelope = EnvelopeFactory.create(
            body=result, produced_by=str(node.id), trace_id=request.execution_id or ""
        )

        current_cache_key = request.get_handler_state("current_cache_key")
        current_ir_data = request.get_handler_state("current_ir_data")

        meta_dict = {
            "builder_type": node.builder_type,
            "cache_key": current_cache_key,
            "cached": node.cache_enabled,
            "validated": node.validate_output,
        }

        if current_ir_data and hasattr(current_ir_data, "metadata"):
            meta_dict["ir_metadata"] = current_ir_data.metadata.dict()

        envelope = envelope.with_meta(**meta_dict)

        return envelope
