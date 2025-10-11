"""Handler for Integrated API node."""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry import API_KEY_SERVICE, INTEGRATED_API_SERVICE
from dipeo.diagram_generated.unified_nodes.integrated_api_node import IntegratedApiNode, NodeType
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass


@register_handler
@requires_services(integrated_api_service=INTEGRATED_API_SERVICE, api_key_service=API_KEY_SERVICE)
class IntegratedApiNodeHandler(TypedNodeHandler[IntegratedApiNode]):
    """Handler for executing integrated API operations across multiple providers."""

    NODE_TYPE = NodeType.INTEGRATED_API

    def __init__(self):
        super().__init__()

    @property
    def node_class(self) -> type[IntegratedApiNode]:
        return IntegratedApiNode

    @property
    def node_type(self) -> str:
        return NodeType.INTEGRATED_API.value

    @property
    def schema(self) -> type[BaseModel]:
        return IntegratedApiNode

    @property
    def description(self) -> str:
        return "Executes operations on various API providers (Notion, Slack, GitHub, etc.)"

    async def pre_execute(self, request: ExecutionRequest[IntegratedApiNode]) -> Envelope | None:
        node = request.node

        # Get services from request
        integrated_api_service = request.get_optional_service(INTEGRATED_API_SERVICE)
        api_key_service = request.get_optional_service(API_KEY_SERVICE)

        if not integrated_api_service:
            return EnvelopeFactory.create(
                body={"error": "Integrated API service not available", "type": "ValueError"},
                produced_by=str(node.id),
            )

        if not api_key_service:
            return EnvelopeFactory.create(
                body={"error": "API key service not available", "type": "ValueError"},
                produced_by=str(node.id),
            )

        provider = node.provider
        operation = node.operation

        if hasattr(provider, "value"):
            provider = provider.value

        api_keys = api_key_service.list_api_keys()
        provider_summary = next((k for k in api_keys if k["service"] == provider), None)

        if not provider_summary:
            return EnvelopeFactory.create(
                body={
                    "error": f"No API key configured for provider '{provider}'",
                    "type": "ValueError",
                },
                produced_by=str(node.id),
            )

        provider_key = api_key_service.get_api_key(provider_summary["id"])
        api_key = provider_key["key"]

        config = node.config or {}
        try:
            is_valid = await integrated_api_service.validate_operation(
                provider=provider, operation=operation, config=config
            )
        except Exception as e:
            return EnvelopeFactory.create(
                body={
                    "error": f"Validation error for provider '{provider}' op '{operation}': {e}",
                    "type": "ValueError",
                },
                produced_by=str(node.id),
            )

        if not is_valid:
            return EnvelopeFactory.create(
                body={
                    "error": f"Unsupported provider/operation or invalid config: {provider}.{operation}",
                    "type": "ValueError",
                },
                produced_by=str(node.id),
            )

        request.set_handler_state("api_key", api_key)
        request.set_handler_state("provider", provider)
        request.set_handler_state("operation", operation)

        return None

    async def run(
        self, inputs: dict[str, Any], request: ExecutionRequest[IntegratedApiNode]
    ) -> dict[str, Any]:
        envelope_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, dict):
                envelope_inputs[key] = EnvelopeFactory.create(body=value, produced_by="input")
            else:
                envelope_inputs[key] = EnvelopeFactory.create(body=str(value), produced_by="input")

        result_envelope = await self._execute_api_operation(request, envelope_inputs)

        if result_envelope.content_type == "object":
            return result_envelope.as_json()
        else:
            return {"result": result_envelope.as_text()}

    async def _execute_api_operation(
        self, request: ExecutionRequest[IntegratedApiNode], envelope_inputs: dict[str, Envelope]
    ) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        integrated_api_service = self._integrated_api_service
        api_key = request.get_handler_state("api_key")
        provider = request.get_handler_state("provider")
        operation = request.get_handler_state("operation")

        config = node.config or {}

        if envelope_inputs:
            if default_envelope := self.get_optional_input(envelope_inputs, "default"):
                try:
                    default_input = default_envelope.as_json()
                    if isinstance(default_input, dict):
                        config = {**config, **default_input}
                    else:
                        config["data"] = default_input
                except ValueError:
                    config["data"] = default_envelope.as_text()
            else:
                for key, envelope in envelope_inputs.items():
                    try:
                        config[key] = envelope.as_json()
                    except ValueError:
                        config[key] = envelope.as_text()

        resource_id = node.resource_id
        timeout = node.timeout or 30
        max_retries = node.max_retries or 3

        logger_context = {
            "provider": provider,
            "operation": operation,
            "resource_id": resource_id,
            "has_config": bool(config),
            "timeout": timeout,
            "max_retries": max_retries,
        }

        result = await integrated_api_service.execute_operation(
            provider=provider,
            operation=operation,
            config=config,
            resource_id=resource_id,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

        output_envelope = EnvelopeFactory.create(
            body=result if isinstance(result, dict) else {"default": result},
            produced_by=node.id,
            trace_id=trace_id,
        ).with_meta(provider=provider, operation=operation)

        return output_envelope

    async def prepare_inputs(
        self, request: ExecutionRequest[IntegratedApiNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        envelope_inputs = self.get_effective_inputs(request, inputs)

        return await super().prepare_inputs(request, envelope_inputs)

    def post_execute(
        self, request: ExecutionRequest[IntegratedApiNode], output: Envelope
    ) -> Envelope:
        self.emit_token_outputs(request, output)

        return output
