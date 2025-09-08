"""Handler for Integrated API node."""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry import API_KEY_SERVICE, INTEGRATED_API_SERVICE
from dipeo.diagram_generated.unified_nodes.integrated_api_node import IntegratedApiNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass


@register_handler
class IntegratedApiNodeHandler(TypedNodeHandler[IntegratedApiNode]):
    """Handler for executing integrated API operations across multiple providers.

    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_with_envelopes() - Core execution logic with envelope inputs

    Now uses envelope-based communication for clean input/output interfaces.
    """

    NODE_TYPE = NodeType.INTEGRATED_API

    def __init__(self):
        super().__init__()
        # Instance variables for passing data between methods
        self._current_integrated_api_service = None
        self._current_api_key_service = None
        self._current_api_key = None
        self._current_provider = None
        self._current_operation = None

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
    def requires_services(self) -> list[str]:
        return ["integrated_api_service", "api_key_service"]

    @property
    def description(self) -> str:
        return "Executes operations on various API providers (Notion, Slack, GitHub, etc.)"

    async def pre_execute(self, request: ExecutionRequest[IntegratedApiNode]) -> Envelope | None:
        """Pre-execution setup: validate services and API key availability.

        Moves service checks, API key validation, and provider resolution
        out of execute_request for cleaner separation of concerns.
        """
        node = request.node

        # Get services from ServiceRegistry
        integrated_api_service = request.services.resolve(INTEGRATED_API_SERVICE)
        api_key_service = request.services.resolve(API_KEY_SERVICE)

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

        # Get the API key for the provider
        provider = node.provider
        operation = node.operation

        # Handle enum values
        if hasattr(provider, "value"):
            provider = provider.value

        # Get API key from the key service
        # First find the key ID for this provider
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

        # Now get the full key details including the actual key
        provider_key = api_key_service.get_api_key(provider_summary["id"])
        api_key = provider_key["key"]

        # Validate provider/operation dynamically via registry
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

        # Store services and API key in instance variables for execute_request
        self._current_integrated_api_service = integrated_api_service
        self._current_api_key_service = api_key_service
        self._current_api_key = api_key
        self._current_provider = provider
        self._current_operation = operation

        # No early return - proceed to execute_request
        return None

    async def run(
        self, inputs: dict[str, Any], request: ExecutionRequest[IntegratedApiNode]
    ) -> dict[str, Any]:
        """Execute integrated API operation."""
        # Convert legacy dict inputs back to envelopes for the existing implementation
        envelope_inputs = {}
        for key, value in inputs.items():
            if isinstance(value, dict):
                envelope_inputs[key] = EnvelopeFactory.create(body=value, produced_by="input")
            else:
                envelope_inputs[key] = EnvelopeFactory.create(body=str(value), produced_by="input")

        # Use existing implementation
        result_envelope = await self._execute_api_operation(request, envelope_inputs)

        # Return the result as dict for the base class to serialize
        if result_envelope.content_type == "object":
            return result_envelope.as_json()
        else:
            return {"result": result_envelope.as_text()}

    async def _execute_api_operation(
        self, request: ExecutionRequest[IntegratedApiNode], envelope_inputs: dict[str, Envelope]
    ) -> Envelope:
        """Execute the API operation through the integrated service."""

        # Extract properties from request
        node = request.node
        trace_id = request.execution_id or ""

        # Use pre-validated services and API key from instance variables (set in pre_execute)
        integrated_api_service = self._current_integrated_api_service
        api_key = self._current_api_key
        provider = self._current_provider
        operation = self._current_operation

        # Prepare configuration
        config = node.config or {}

        # Merge any input data from envelopes into config
        if envelope_inputs:
            # Check for default input envelope
            if default_envelope := self.get_optional_input(envelope_inputs, "default"):
                try:
                    default_input = default_envelope.as_json()
                    if isinstance(default_input, dict):
                        config = {**config, **default_input}
                    else:
                        config["data"] = default_input
                except ValueError:
                    # Fall back to text if not JSON
                    config["data"] = default_envelope.as_text()
            else:
                # Process all inputs and add to config
                for key, envelope in envelope_inputs.items():
                    try:
                        config[key] = envelope.as_json()
                    except ValueError:
                        config[key] = envelope.as_text()

        # Get optional parameters
        resource_id = node.resource_id
        timeout = node.timeout or 30
        max_retries = node.max_retries or 3

        # Debug logging
        logger_context = {
            "provider": provider,
            "operation": operation,
            "resource_id": resource_id,
            "has_config": bool(config),
            "timeout": timeout,
            "max_retries": max_retries,
        }
        # Debug: Executing integrated API operation

        try:
            # Execute the operation
            result = await integrated_api_service.execute_operation(
                provider=provider,
                operation=operation,
                config=config,
                resource_id=resource_id,
                api_key=api_key,
                timeout=timeout,
                max_retries=max_retries,
            )

            # Successfully executed operation

            # Create output envelope
            output_envelope = EnvelopeFactory.create(
                body=result if isinstance(result, dict) else {"default": result},
                produced_by=node.id,
                trace_id=trace_id,
            ).with_meta(provider=provider, operation=operation)

            return output_envelope

        except ValueError as e:
            # Configuration or validation errors
            # Validation error
            error_envelope = EnvelopeFactory.create(
                body=str(e), produced_by=node.id, trace_id=trace_id
            ).with_meta(error_type="ValidationError", provider=provider, operation=operation)
            return EnvelopeFactory.create(
                body={"error": str(e), "type": "ValidationError"},
                produced_by=str(node.id),
                trace_id=trace_id,
            )

        except Exception as e:
            # Other errors
            # API operation failed
            error_envelope = EnvelopeFactory.create(
                body=str(e), produced_by=node.id, trace_id=trace_id
            ).with_meta(error_type=type(e).__name__, provider=provider, operation=operation)
            return EnvelopeFactory.create(
                body={"error": str(e), "type": e.__class__.__name__},
                produced_by=str(node.id),
                trace_id=trace_id,
            )

    async def prepare_inputs(
        self, request: ExecutionRequest[IntegratedApiNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs with token consumption.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.consume_token_inputs(request, inputs)

        # Call parent prepare_inputs for default envelope conversion
        return await super().prepare_inputs(request, envelope_inputs)

    def post_execute(
        self, request: ExecutionRequest[IntegratedApiNode], output: Envelope
    ) -> Envelope:
        """Post-execution hook to emit tokens.

        Phase 5: Now emits output as tokens to trigger downstream nodes.
        """
        # Phase 5: Emit output as tokens to trigger downstream nodes
        self.emit_token_outputs(request, output)

        return output
