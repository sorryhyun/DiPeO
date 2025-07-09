"""API job node handler - makes HTTP requests to external APIs."""

import asyncio
import json
from typing import Any

from dipeo.application import BaseNodeHandler, register_handler
from dipeo.core.ports.execution_context import ExecutionContextPort
from dipeo.application.utils import create_node_output
from dipeo.models import ApiJobNodeData, NodeOutput, HttpMethod
from pydantic import BaseModel


@register_handler
class ApiJobNodeHandler(BaseNodeHandler):
    """Handler for api_job nodes - makes HTTP requests."""
    
    def __init__(self, api_service=None):
        """Initialize with injected services."""
        self.api_service = api_service

    @property
    def node_type(self) -> str:
        return "api_job"

    @property
    def schema(self) -> type[BaseModel]:
        return ApiJobNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["api_service"]

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
        """Execute API job node using the infrastructure API service."""
        # Use injected service or fall back to old pattern for backward compatibility
        api_service = self.api_service
        if not api_service:
            api_service = context.get_service("api_service")
            if not api_service:
                api_service = services.get("api_service")
            
        if not api_service:
            return create_node_output(
                {"default": ""}, 
                {"error": "API service not available"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
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
            # Parse JSON strings for headers, params, body, and auth_config
            parsed_data = self._parse_json_inputs(headers, params, body, auth_config)
            if "error" in parsed_data:
                return create_node_output(
                    {"default": ""}, 
                    {"error": parsed_data["error"]},
                    node_id=context.current_node_id,
                    executed_nodes=context.executed_nodes
                )
            
            headers = parsed_data["headers"]
            params = parsed_data["params"]
            body = parsed_data["body"]
            auth_config = parsed_data["auth_config"]

            # Prepare authentication
            auth = self._prepare_auth(auth_type, auth_config)
            
            # Apply bearer token or API key to headers if needed
            headers = self._apply_auth_headers(headers, auth_type, auth_config)
            
            # Prepare request data based on method and params
            request_data = self._prepare_request_data(method, params, body)
            
            # Execute request using API service with retry logic
            response_data = await api_service.execute_with_retry(
                url=url,
                method=method.value,
                data=request_data,
                headers=headers,
                max_retries=props.max_retries if hasattr(props, "max_retries") else 3,
                retry_delay=1.0,
                timeout=timeout,
                auth=auth,
                expected_status_codes=list(range(200, 300))  # 2xx status codes
            )
            
            # Format output
            output_value = json.dumps(response_data) if isinstance(response_data, dict) else str(response_data)
            
            return create_node_output(
                {"default": output_value},
                {
                    "success": True,
                    "url": url,
                    "method": method.value
                },
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )

        except Exception as e:
            # API service handles retries and specific errors
            # This catches any remaining errors
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

    def _parse_json_inputs(
        self, headers: Any, params: Any, body: Any, auth_config: Any
    ) -> dict[str, Any]:
        """Parse JSON string inputs into Python objects."""
        result = {
            "headers": headers or {},
            "params": params or {},
            "body": body,
            "auth_config": auth_config or {}
        }
        
        # Parse headers if provided as JSON string
        if isinstance(headers, str):
            try:
                result["headers"] = json.loads(headers)
            except json.JSONDecodeError:
                return {"error": "Invalid headers JSON format"}
        
        # Parse params if provided as JSON string
        if isinstance(params, str):
            try:
                result["params"] = json.loads(params)
            except json.JSONDecodeError:
                return {"error": "Invalid params JSON format"}
        
        # Parse body if provided as JSON string
        if isinstance(body, str) and body.strip():
            try:
                result["body"] = json.loads(body)
            except json.JSONDecodeError:
                # Keep as string if not JSON
                pass
        
        # Parse auth config if provided as JSON string
        if isinstance(auth_config, str) and auth_config.strip():
            try:
                result["auth_config"] = json.loads(auth_config)
            except json.JSONDecodeError:
                return {"error": "Invalid auth_config JSON format"}
        
        return result
    
    def _prepare_auth(self, auth_type: str, auth_config: dict) -> dict[str, str] | None:
        """Prepare authentication dictionary for API service.
        
        Note: For bearer and API key auth, we'll apply them directly to headers
        since the API service expects basic auth format for the auth parameter.
        """
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
        """Prepare request data based on method."""
        # For GET requests, params are query parameters (handled separately)
        if method == HttpMethod.GET:
            return None
            
        # For other methods, return body data
        if body is not None:
            return body
            
        # If no body but params exist for POST/PUT/PATCH, use params as body
        if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH] and params:
            return params
            
        return None
    
    def _apply_auth_headers(self, headers: dict, auth_type: str, auth_config: dict) -> dict:
        """Apply authentication to headers for bearer token and API key."""
        headers = headers.copy()  # Don't modify original
        
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