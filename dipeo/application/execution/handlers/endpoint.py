import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import Optional, requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.execution.handlers.utils import create_error_body, serialize_data
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes.endpoint_node import EndpointNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass


@register_handler
@requires_services(filesystem_adapter=(FILESYSTEM_ADAPTER, Optional))
class EndpointNodeHandler(TypedNodeHandler[EndpointNode]):
    """Endpoint node - pass through data and optionally save to file."""

    NODE_TYPE = NodeType.ENDPOINT

    def __init__(self):
        super().__init__()

    @property
    def node_class(self) -> type[EndpointNode]:
        return EndpointNode

    @property
    def node_type(self) -> str:
        return NodeType.ENDPOINT.value

    @property
    def schema(self) -> type[BaseModel]:
        return EndpointNode

    @property
    def description(self) -> str:
        return "Endpoint node - pass through data and optionally save to file"

    async def pre_execute(self, request: ExecutionRequest[EndpointNode]) -> Envelope | None:
        node = request.node
        services = request.services

        if node.save_to_file:
            filesystem_adapter = request.get_optional_service(FILESYSTEM_ADAPTER)

            if not filesystem_adapter:
                return EnvelopeFactory.create(
                    body=create_error_body(
                        "Filesystem adapter is required when save_to_file is enabled"
                    ),
                    produced_by=str(node.id),
                )

            file_name = node.file_name

            if not file_name and hasattr(node, "metadata") and node.metadata:
                file_name = node.metadata.get("file_path")

            if not file_name:
                pass

            if not file_name:
                file_name = f"output_{node.id}.json"

            request.set_handler_state("save_enabled", True)
            request.set_handler_state("filename", file_name)
            request.set_handler_state("filesystem_adapter", filesystem_adapter)
        else:
            request.set_handler_state("save_enabled", False)
            request.set_handler_state("filename", None)

        return None

    def validate(self, request: ExecutionRequest[EndpointNode]) -> str | None:
        node = request.node
        filesystem_adapter = request.get_optional_service(FILESYSTEM_ADAPTER)

        if node.save_to_file and not filesystem_adapter:
            return "Filesystem adapter is required when save_to_file is enabled"

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[EndpointNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs with token consumption."""
        # Use standard pattern for token inputs
        envelope_inputs = self.get_effective_inputs(request, inputs)

        result_data = {}
        for key, envelope in envelope_inputs.items():
            try:
                result_data[key] = envelope.as_json()
            except ValueError:
                result_data[key] = envelope.as_text()

        if len(result_data) == 1 and "default" in result_data:
            result_data = result_data["default"]

        return {"data": result_data}

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[EndpointNode]) -> Any:
        result_data = inputs.get("data", {})

        save_enabled = request.get_handler_state("save_enabled", False)
        if save_enabled:
            file_name = request.get_handler_state("filename")
            filesystem_adapter = request.get_handler_state("filesystem_adapter")

            if filesystem_adapter:
                try:
                    content = serialize_data(
                        result_data, "json" if isinstance(result_data, dict) else "text"
                    )

                    file_path = Path(file_name)
                    parent_dir = file_path.parent
                    if parent_dir != Path() and not filesystem_adapter.exists(parent_dir):
                        filesystem_adapter.mkdir(parent_dir, parents=True)

                    with filesystem_adapter.open(file_path, "wb") as f:
                        f.write(content.encode("utf-8"))

                    return {"data": result_data, "saved_to": file_name, "save_success": True}
                except Exception as exc:
                    raise Exception(f"Failed to save to file {file_name}: {exc!s}") from exc

        return {"data": result_data, "saved_to": None, "save_success": False}

    def serialize_output(self, result: Any, request: ExecutionRequest[EndpointNode]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        result_data = result.get("data", {})
        saved_to = result.get("saved_to")

        output_envelope = EnvelopeFactory.create(
            body=result_data if isinstance(result_data, dict) else {"default": result_data},
            produced_by=node.id,
            trace_id=trace_id,
        )

        if saved_to:
            output_envelope = output_envelope.with_meta(saved_to=saved_to)

        return output_envelope

    def post_execute(self, request: ExecutionRequest[EndpointNode], output: Envelope) -> Envelope:
        """Post-execution hook to emit tokens."""
        self.emit_token_outputs(request, output)
        return output
