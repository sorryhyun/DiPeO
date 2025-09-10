import contextlib
import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry import API_INVOKER
from dipeo.diagram_generated.enums import HttpMethod
from dipeo.diagram_generated.unified_nodes.api_job_node import ApiJobNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass


@register_handler
class ApiJobNodeHandler(TypedNodeHandler[ApiJobNode]):
    """
    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_with_envelopes() - Core execution logic with envelope inputs

    Now uses envelope-based communication for clean input/output interfaces.
    """

    NODE_TYPE = NodeType.API_JOB

    def __init__(self):
        super().__init__()
        # Instance variables for passing data between methods
        self._current_api_service = None
        self._current_method = None
        self._current_headers = None
        self._current_params = None
        self._current_body = None
        self._current_auth_config = None

    @property
    def node_class(self) -> type[ApiJobNode]:
        return ApiJobNode

    @property
    def node_type(self) -> str:
        return NodeType.API_JOB.value

    @property
    def schema(self) -> type[BaseModel]:
        return ApiJobNode

    @property
    def requires_services(self) -> list[str]:
        return ["api_service"]

    @property
    def description(self) -> str:
        return "Makes HTTP requests to external APIs with authentication support"

    async def pre_execute(self, request: ExecutionRequest[ApiJobNode]) -> Envelope | None:
        """Pre-execution validation and setup."""
        node = request.node

        # Check service availability
        api_service = request.services.resolve(API_INVOKER)
        if not api_service:
            return EnvelopeFactory.create(
                body={"error": "API service not available", "type": "RuntimeError"},
                produced_by=str(node.id),
            )

        # Validate URL
        if not node.url:
            return EnvelopeFactory.create(
                body={"error": "No URL provided", "type": "ValueError"}, produced_by=str(node.id)
            )

        # Convert and validate HTTP method
        method = node.method
        if isinstance(method, str):
            try:
                method = HttpMethod(method.upper())
            except ValueError:
                return EnvelopeFactory.create(
                    body={"error": f"Invalid HTTP method: {method}", "type": "ValueError"},
                    produced_by=str(node.id),
                )

        # Parse and validate JSON inputs
        headers = node.headers or {}
        params = node.params or {}
        body = node.body
        auth_config = node.auth_config or {}

        parsed_data = self._parse_json_inputs(headers, params, body, auth_config)
        if "error" in parsed_data:
            return EnvelopeFactory.create(
                body={"error": parsed_data["error"], "type": "ValueError"}, produced_by=str(node.id)
            )

        # Store validated data in instance variables for execute_request to use
        self._current_api_service = api_service
        self._current_method = method
        self._current_headers = parsed_data["headers"]
        self._current_params = parsed_data["params"]
        self._current_body = parsed_data["body"]
        self._current_auth_config = parsed_data["auth_config"]

        # Return None to proceed with normal execution
        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[ApiJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare API request inputs from envelopes and node configuration.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        node = request.node

        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.consume_token_inputs(request, inputs)

        # Start with pre-validated data from instance variables (set in pre_execute)
        api_config = {
            "api_service": self._current_api_service,
            "method": self._current_method,
            "headers": self._current_headers.copy(),
            "params": self._current_params.copy(),
            "body": self._current_body,
            "auth_config": self._current_auth_config,
            "url": node.url,
            "timeout": node.timeout or 30,
            "auth_type": node.auth_type or "none",
        }

        # Process any dynamic inputs from envelopes
        if url_envelope := self.get_optional_input(envelope_inputs, "url"):
            api_config["url"] = url_envelope.as_text()

        if headers_envelope := self.get_optional_input(envelope_inputs, "headers"):
            try:
                api_config["headers"] = headers_envelope.as_json()
            except ValueError:
                headers_text = headers_envelope.as_text()
                try:
                    api_config["headers"] = json.loads(headers_text)
                except json.JSONDecodeError as e:
                    raise ValueError("Invalid headers format in input") from e

        if params_envelope := self.get_optional_input(envelope_inputs, "params"):
            try:
                api_config["params"] = params_envelope.as_json()
            except ValueError:
                params_text = params_envelope.as_text()
                try:
                    api_config["params"] = json.loads(params_text)
                except json.JSONDecodeError as e:
                    raise ValueError("Invalid params format in input") from e

        if body_envelope := self.get_optional_input(envelope_inputs, "body"):
            try:
                api_config["body"] = body_envelope.as_json()
            except ValueError:
                api_config["body"] = body_envelope.as_text()

        return api_config

    async def run(
        self, inputs: dict[str, Any], request: ExecutionRequest[ApiJobNode]
    ) -> dict[str, Any]:
        """Execute API request."""
        node = request.node
        api_config = inputs

        # Extract configuration
        api_service = api_config["api_service"]
        method = api_config["method"]
        headers = api_config["headers"]
        params = api_config["params"]
        body = api_config["body"]
        auth_config = api_config["auth_config"]
        url = api_config["url"]
        timeout = api_config["timeout"]
        auth_type = api_config["auth_type"]

        print(f"[ApiJobNode] URL: {url}")
        print(f"[ApiJobNode] Method: {method}")
        print(f"[ApiJobNode] Headers: {headers}")

        auth = self._prepare_auth(auth_type, auth_config)
        headers = self._apply_auth_headers(headers, auth_type, auth_config)
        request_data = self._prepare_request_data(method, params, body)

        method_value = method.value if hasattr(method, "value") else str(method)

        response_data = await api_service.execute_with_retry(
            url=url,
            method=method_value,
            data=request_data,
            headers=headers,
            max_retries=node.max_retries if hasattr(node, "max_retries") else 3,
            retry_delay=1.0,
            timeout=timeout,
            auth=auth,
            expected_status_codes=list(range(200, 300)),
        )

        # Store raw response data for building representations
        if hasattr(api_service, "last_response"):
            self._last_response = api_service.last_response
        else:
            self._last_response = None

        # Convert response to dict format and include metadata
        response_dict = (
            response_data if isinstance(response_data, dict) else {"result": str(response_data)}
        )
        response_dict["_api_meta"] = {
            "url": url,
            "method": method_value,
            "status_code": 200,  # Default success code
            "request_headers": headers,
            "response_headers": getattr(self._last_response, "headers", {})
            if self._last_response
            else {},
        }

        return response_dict

    def _build_node_output(self, result: Any, request: ExecutionRequest[ApiJobNode]) -> Envelope:
        """
        Build a single-envelope output for API responses.
        Uses auto-detection to determine the appropriate content type.
        """
        node = request.node
        trace_id = request.execution_id or ""

        # Extract metadata if present
        meta = result.pop("_api_meta", {}) if isinstance(result, dict) else {}

        # Prepare HTTP metadata
        http_meta = {
            "status": meta.get("status_code", 200),
            "url": meta.get("url", node.url),
            "method": meta.get(
                "method",
                str(self._current_method)
                if hasattr(self, "_current_method")
                else getattr(node, "method", None),
            ),
            "request_headers": meta.get("request_headers"),
            "response_headers": meta.get("response_headers"),
        }

        # Use EnvelopeFactory.create() with auto-detection
        env = EnvelopeFactory.create(
            body=result,  # Let EnvelopeFactory auto-detect the content type
            produced_by=str(node.id),
            trace_id=trace_id,
            meta={"http": http_meta},
        )
        return env

    def serialize_output(self, result: Any, request: ExecutionRequest[ApiJobNode]) -> Envelope:
        """Return a single Envelope with typed meta."""
        return self._build_node_output(result, request)

    def _parse_json_inputs(
        self, headers: Any, params: Any, body: Any, auth_config: Any
    ) -> dict[str, Any]:
        result = {
            "headers": headers or {},
            "params": params or {},
            "body": body,
            "auth_config": auth_config or {},
        }

        if isinstance(headers, str):
            try:
                result["headers"] = json.loads(headers)
            except json.JSONDecodeError:
                return {"error": "Invalid headers JSON format"}

        if isinstance(params, str):
            try:
                result["params"] = json.loads(params)
            except json.JSONDecodeError:
                return {"error": "Invalid params JSON format"}

        if isinstance(body, str) and body.strip():
            with contextlib.suppress(json.JSONDecodeError):
                result["body"] = json.loads(body)

        if isinstance(auth_config, str) and auth_config.strip():
            try:
                result["auth_config"] = json.loads(auth_config)
            except json.JSONDecodeError:
                return {"error": "Invalid auth_config JSON format"}

        return result

    def _prepare_auth(self, auth_type: str, auth_config: dict) -> dict[str, str] | None:
        if auth_type == "none":
            return None

        if auth_type == "basic":
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            if username and password:
                return {"username": username, "password": password}

        # For bearer and API key, we'll handle them in headers instead
        return None

    def _prepare_request_data(
        self, method: HttpMethod, params: dict, body: Any
    ) -> dict[str, Any] | None:
        if method == HttpMethod.GET:
            return None

        if body is not None:
            return body

        if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH] and params:
            return params

        return None

    def _apply_auth_headers(self, headers: dict, auth_type: str, auth_config: dict) -> dict:
        headers = headers.copy()

        if auth_type == "bearer":
            token = auth_config.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key":
            key_name = auth_config.get("key_name", "X-API-Key")
            key_value = auth_config.get("key_value", "")
            if key_value:
                headers[key_name] = key_value

        return headers

    def post_execute(self, request: ExecutionRequest[ApiJobNode], output: Envelope) -> Envelope:
        """Post-execution hook to emit tokens.

        Phase 5: Now emits output as tokens to trigger downstream nodes.
        """
        # Phase 5: Emit output as tokens to trigger downstream nodes
        self.emit_token_outputs(request, output)

        # Post-execution logging can use node properties or output fields
        # No need for metadata access
        return output

    async def on_error(
        self, request: ExecutionRequest[ApiJobNode], error: Exception
    ) -> Envelope | None:
        # Use node properties for error context
        url = request.node.url or "unknown"
        method = (
            str(self._current_method) if self._current_method else request.node.method or "unknown"
        )

        return EnvelopeFactory.create(
            body={"error": str(error), "type": error.__class__.__name__},
            produced_by=str(request.node.id),
        )
