"""API job node handler - makes HTTP requests to external APIs."""

import asyncio
import json
from typing import Any
import httpx

from dipeo.application import BaseNodeHandler, register_handler
from dipeo.domain.services.ports.execution_context import ExecutionContextPort
from dipeo.application.utils import create_node_output
from dipeo.models import ApiJobNodeData, NodeOutput, HttpMethod
from pydantic import BaseModel


@register_handler
class ApiJobNodeHandler(BaseNodeHandler):
    """Handler for api_job nodes - makes HTTP requests."""

    @property
    def node_type(self) -> str:
        return "api_job"

    @property
    def schema(self) -> type[BaseModel]:
        return ApiJobNodeData

    @property
    def description(self) -> str:
        return "Makes HTTP requests to external APIs with authentication support"

    async def execute(
        self,
        props: ApiJobNodeData,
        context: ExecutionContextPort,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute API job node."""
        url = props.url
        method = props.method
        headers = props.headers or {}
        params = props.params or {}
        body = props.body
        timeout = props.timeout or 30
        auth_type = props.auth_type or "none"
        auth_config = props.auth_config or {}

        if not url:
            return create_node_output(
                {"default": ""}, 
                {"error": "No URL provided"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )

        try:
            # Parse headers if provided as JSON string
            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    return create_node_output(
                        {"default": ""}, 
                        {"error": "Invalid headers JSON format"},
                        node_id=context.current_node_id,
                        executed_nodes=context.executed_nodes
                    )

            # Parse params if provided as JSON string
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except json.JSONDecodeError:
                    return create_node_output(
                        {"default": ""}, 
                        {"error": "Invalid params JSON format"},
                        node_id=context.current_node_id,
                        executed_nodes=context.executed_nodes
                    )

            # Parse body if provided as JSON string
            if isinstance(body, str) and body.strip():
                try:
                    body = json.loads(body)
                except json.JSONDecodeError:
                    # Keep as string if not JSON
                    pass

            # Parse auth config if provided as JSON string
            if isinstance(auth_config, str) and auth_config.strip():
                try:
                    auth_config = json.loads(auth_config)
                except json.JSONDecodeError:
                    return create_node_output(
                        {"default": ""}, 
                        {"error": "Invalid auth_config JSON format"},
                        node_id=context.current_node_id,
                        executed_nodes=context.executed_nodes
                    )

            # Apply authentication
            headers = self._apply_auth(headers, auth_type, auth_config)

            # Make the HTTP request
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await self._make_request(
                    client, method, url, headers, params, body
                )

            # Process response
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }

            # Try to parse response as JSON
            try:
                result["data"] = response.json()
            except:
                result["data"] = response.text

            # Return success if status code is 2xx
            if 200 <= response.status_code < 300:
                return create_node_output(
                    {"default": json.dumps(result["data"]) if isinstance(result["data"], dict) else result["data"]},
                    {
                        "status_code": response.status_code,
                        "success": True,
                        "url": url,
                        "method": method.value
                    },
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )
            else:
                return create_node_output(
                    {"default": ""},
                    {
                        "error": f"HTTP {response.status_code}: {result.get('data', 'Unknown error')}",
                        "status_code": response.status_code,
                        "success": False,
                        "url": url,
                        "method": method.value
                    },
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )

        except asyncio.TimeoutError:
            return create_node_output(
                {"default": ""}, 
                {
                    "error": f"Request timed out after {timeout} seconds",
                    "success": False,
                    "url": url,
                    "method": method.value
                },
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        except Exception as e:
            return create_node_output(
                {"default": ""}, 
                {
                    "error": str(e),
                    "success": False,
                    "url": url,
                    "method": method.value
                },
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )

    def _apply_auth(self, headers: dict, auth_type: str, auth_config: dict) -> dict:
        """Apply authentication to headers based on auth type."""
        headers = headers.copy()  # Don't modify original

        if auth_type == "bearer":
            token = auth_config.get("token", "")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "basic":
            username = auth_config.get("username", "")
            password = auth_config.get("password", "")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
        elif auth_type == "api_key":
            key_name = auth_config.get("key_name", "X-API-Key")
            key_value = auth_config.get("key_value", "")
            if key_value:
                headers[key_name] = key_value

        return headers

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        method: HttpMethod,
        url: str,
        headers: dict,
        params: dict,
        body: Any
    ) -> httpx.Response:
        """Make the actual HTTP request."""
        kwargs = {
            "url": url,
            "headers": headers,
            "params": params,
        }

        # Add body for methods that support it
        if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
            if isinstance(body, dict):
                kwargs["json"] = body
            elif body is not None:
                kwargs["data"] = body

        # Make the request based on method
        if method == HttpMethod.GET:
            return await client.get(**kwargs)
        elif method == HttpMethod.POST:
            return await client.post(**kwargs)
        elif method == HttpMethod.PUT:
            return await client.put(**kwargs)
        elif method == HttpMethod.DELETE:
            return await client.delete(**kwargs)
        elif method == HttpMethod.PATCH:
            return await client.patch(**kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")