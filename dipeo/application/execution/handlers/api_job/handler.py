import json
from typing import Any

from pydantic import BaseModel

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.handlers.api_job.request_builder import (
    apply_auth_headers,
    parse_json_inputs,
    prepare_auth,
    prepare_request_data,
)
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry import API_INVOKER
from dipeo.diagram_generated.enums import HttpMethod
from dipeo.diagram_generated.unified_nodes.api_job_node import ApiJobNode, NodeType
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory


@register_handler
@requires_services(
    api_service=API_INVOKER,
)
class ApiJobNodeHandler(TypedNodeHandler[ApiJobNode]):
    """Handler for API job nodes with authentication and retry support."""

    NODE_TYPE = NodeType.API_JOB

    def __init__(self):
        super().__init__()

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
    def description(self) -> str:
        return "Makes HTTP requests to external APIs with authentication support"

    async def pre_execute(self, request: ExecutionRequest[ApiJobNode]) -> Envelope | None:
        node = request.node

        if not node.url:
            return EnvelopeFactory.create(
                body={"error": "No URL provided", "type": "ValueError"}, produced_by=str(node.id)
            )

        method = node.method
        if isinstance(method, str):
            try:
                method = HttpMethod(method.upper())
            except ValueError:
                return EnvelopeFactory.create(
                    body={"error": f"Invalid HTTP method: {method}", "type": "ValueError"},
                    produced_by=str(node.id),
                )

        headers = node.headers or {}
        params = node.params or {}
        body = node.body
        auth_config = node.auth_config or {}

        parsed_data = parse_json_inputs(headers, params, body, auth_config)
        if "error" in parsed_data:
            return EnvelopeFactory.create(
                body={"error": parsed_data["error"], "type": "ValueError"}, produced_by=str(node.id)
            )

        request.set_handler_state("method", method)
        request.set_handler_state("headers", parsed_data["headers"])
        request.set_handler_state("params", parsed_data["params"])
        request.set_handler_state("body", parsed_data["body"])
        request.set_handler_state("auth_config", parsed_data["auth_config"])

        return None

    async def prepare_inputs(
        self, request: ExecutionRequest[ApiJobNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        node = request.node

        envelope_inputs = self.get_effective_inputs(request, inputs)

        api_config = {
            "method": request.get_handler_state("method"),
            "headers": request.get_handler_state("headers", {}).copy(),
            "params": request.get_handler_state("params", {}).copy(),
            "body": request.get_handler_state("body"),
            "auth_config": request.get_handler_state("auth_config", {}),
            "url": node.url,
            "timeout": node.timeout or 30,
            "auth_type": node.auth_type or "none",
        }

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
        node = request.node
        api_config = inputs

        api_service = self._api_service
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

        auth = prepare_auth(auth_type, auth_config)
        headers = apply_auth_headers(headers, auth_type, auth_config)
        request_data = prepare_request_data(method, params, body)

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

        if hasattr(api_service, "last_response"):
            request.set_handler_state("last_response", api_service.last_response)
        else:
            request.set_handler_state("last_response", None)

        last_response = request.get_handler_state("last_response")
        response_dict = (
            response_data if isinstance(response_data, dict) else {"result": str(response_data)}
        )
        response_dict["_api_meta"] = {
            "url": url,
            "method": method_value,
            "status_code": 200,
            "request_headers": headers,
            "response_headers": getattr(last_response, "headers", {}) if last_response else {},
        }

        return response_dict

    def serialize_output(self, result: Any, request: ExecutionRequest[ApiJobNode]) -> Envelope:
        node = request.node
        trace_id = request.execution_id or ""

        meta = result.pop("_api_meta", {}) if isinstance(result, dict) else {}

        current_method = request.get_handler_state("method")
        http_meta = {
            "status": meta.get("status_code", 200),
            "url": meta.get("url", node.url),
            "method": meta.get(
                "method",
                str(current_method) if current_method else getattr(node, "method", None),
            ),
            "request_headers": meta.get("request_headers"),
            "response_headers": meta.get("response_headers"),
        }

        env = EnvelopeFactory.create(
            body=result,
            produced_by=str(node.id),
            trace_id=trace_id,
            meta={"http": http_meta},
        )
        return env

    def post_execute(self, request: ExecutionRequest[ApiJobNode], output: Envelope) -> Envelope:
        self.emit_token_outputs(request, output)

        return output

    async def on_error(
        self, request: ExecutionRequest[ApiJobNode], error: Exception
    ) -> Envelope | None:
        url = request.node.url or "unknown"
        current_method = request.get_handler_state("method")
        method = str(current_method) if current_method else request.node.method or "unknown"

        return EnvelopeFactory.create(
            body={"error": str(error), "type": error.__class__.__name__},
            produced_by=str(request.node.id),
        )
