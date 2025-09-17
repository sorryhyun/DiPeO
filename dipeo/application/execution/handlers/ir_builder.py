"""Handler for IR builder nodes."""

import logging
from typing import Any

from pydantic import BaseModel

from dipeo.application.execution.decorators import requires_services
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry.keys import IR_BUILDER_REGISTRY, IR_CACHE, ServiceKey
from dipeo.diagram_generated.unified_nodes.ir_builder_node import IrBuilderNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

logger = logging.getLogger(__name__)


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
        """Initialize the IR builder node handler."""
        super().__init__()
        self._current_builder = None
        self._current_cache_key = None

    @property
    def node_class(self) -> type[IrBuilderNode]:
        """Get the node class this handler manages."""
        return IrBuilderNode

    @property
    def node_type(self) -> str:
        """Get the node type identifier."""
        return NodeType.IR_BUILDER.value

    @property
    def schema(self) -> type[BaseModel]:
        """Get the node schema."""
        return IrBuilderNode

    @property
    def description(self) -> str:
        """Get handler description."""
        return "Builds intermediate representation (IR) from source data"

    def validate(self, request: ExecutionRequest[IrBuilderNode]) -> str | None:
        """Static validation - structural checks only.

        Args:
            request: Execution request with node

        Returns:
            Error message if validation fails, None otherwise
        """
        node = request.node

        # Validate builder type is provided
        if not node.builder_type:
            return "builder_type is required"

        # Validate output format if provided
        if node.output_format and node.output_format not in ["json", "yaml", "raw"]:
            return f"Invalid output_format: {node.output_format}. Must be 'json', 'yaml', or 'raw'"

        return None

    async def pre_execute(self, request: ExecutionRequest[IrBuilderNode]) -> Envelope | None:
        """Runtime validation and setup.

        Args:
            request: Execution request with node

        Returns:
            Error envelope if setup fails, None otherwise
        """
        node = request.node

        try:
            # Get builder from registry and validate it exists
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

            self._current_builder = ir_builder_registry.get_builder(node.builder_type)
            # logger.info(f"Initialized {node.builder_type} IR builder")
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
        """Convert envelope inputs to source data for IR building.

        Args:
            request: Execution request
            inputs: Input envelopes from edges

        Returns:
            Prepared source data
        """
        # Extract source data from the default input
        if "default" in inputs:
            envelope = inputs["default"]
            # Extract the body/data from the envelope
            if hasattr(envelope, "body"):
                return envelope.body
            elif hasattr(envelope, "data"):
                return envelope.data
            else:
                # If it's already a dict, return it
                return inputs.get("default", {})

        # If no default input, return empty dict
        return {}

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[IrBuilderNode]) -> Any:
        """Execute IR building.

        Args:
            inputs: Prepared source data
            request: Execution request

        Returns:
            Built IR data
        """
        node = request.node

        # Generate cache key
        self._current_cache_key = self._current_builder.get_cache_key(inputs)

        # Check cache if enabled
        if node.cache_enabled:
            cached = await self._ir_cache.get(self._current_cache_key)
            if cached:
                logger.info(f"Using cached IR for {node.builder_type}")
                return cached

        # Build IR
        # logger.info(f"Building {node.builder_type} IR from {len(inputs)} source files")
        try:
            ir_data = await self._current_builder.build_ir(inputs)

            # Store the IR data for metadata access in serialize_output
            self._current_ir_data = ir_data

            # Validate if requested
            if node.validate_output:
                if not self._current_builder.validate_ir(ir_data):
                    raise ValueError(f"IR validation failed for {node.builder_type}")
                logger.info(f"IR validation passed for {node.builder_type}")

            # Cache result if enabled
            if node.cache_enabled:
                await self._ir_cache.set(self._current_cache_key, ir_data)
                logger.info(f"Cached IR for {node.builder_type}")

            # Return based on output format
            if node.output_format == "json":
                # For JSON format, merge data fields with metadata at top level
                # Templates expect IR fields at top level but may also need metadata
                if hasattr(ir_data, "data") and hasattr(ir_data, "metadata"):
                    # Merge data fields and metadata at top level
                    result = ir_data.data.copy() if isinstance(ir_data.data, dict) else ir_data.data
                    # Only add IRMetadata if there's no existing metadata field (preserve template metadata)
                    if isinstance(result, dict) and "metadata" not in result:
                        if hasattr(ir_data.metadata, "dict"):
                            # Add metadata as a top-level key
                            result["metadata"] = ir_data.metadata.dict()
                        else:
                            result["metadata"] = ir_data.metadata
                    return result
                elif hasattr(ir_data, "dict"):
                    # Fallback to dict if it's a Pydantic model
                    ir_dict = ir_data.dict()
                    if "data" in ir_dict and "metadata" in ir_dict:
                        # Merge data fields with metadata
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
            elif node.output_format == "yaml":
                # For YAML format, also merge data and metadata
                if hasattr(ir_data, "data") and hasattr(ir_data, "metadata"):
                    result = ir_data.data.copy() if isinstance(ir_data.data, dict) else ir_data.data
                    # Only add IRMetadata if there's no existing metadata field (preserve template metadata)
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
                # Raw format - return as is (keeps full IRData structure)
                return ir_data

        except Exception as e:
            logger.error(f"Failed to build IR: {e}")
            raise

    def serialize_output(self, result: Any, request: ExecutionRequest[IrBuilderNode]) -> Envelope:
        """Serialize IR data to envelope.

        Args:
            result: IR data to serialize
            request: Execution request

        Returns:
            Envelope containing the IR data
        """
        node = request.node

        # Create base envelope
        envelope = EnvelopeFactory.create(
            body=result, produced_by=str(node.id), trace_id=request.execution_id or ""
        )

        # Build metadata - include IR metadata if it was part of the original IRData
        meta_dict = {
            "builder_type": node.builder_type,
            "cache_key": self._current_cache_key,
            "cached": node.cache_enabled,
            "validated": node.validate_output,
        }

        # If we stored the original IRData, extract its metadata
        if hasattr(self, "_current_ir_data") and hasattr(self._current_ir_data, "metadata"):
            meta_dict["ir_metadata"] = self._current_ir_data.metadata.dict()

        # Use ** to unpack the dictionary as keyword arguments
        envelope = envelope.with_meta(**meta_dict)

        return envelope
