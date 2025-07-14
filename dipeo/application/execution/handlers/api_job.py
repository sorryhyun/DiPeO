
import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution import UnifiedExecutionContext
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.core.static.generated_nodes import ApiJobNode
from dipeo.models import ApiJobNodeData, HttpMethod, NodeOutput, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution


@register_handler
class ApiJobNodeHandler(TypedNodeHandler[ApiJobNode]):
    
    def __init__(self, api_service=None):
        self.api_service = api_service

    @property
    def node_class(self) -> type[ApiJobNode]:
        return ApiJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.api_job.value

    @property
    def schema(self) -> type[BaseModel]:
        return ApiJobNodeData
    

    @property
    def requires_services(self) -> list[str]:
        return ["api_service"]

    @property
    def description(self) -> str:
        return "Makes HTTP requests to external APIs with authentication support"

    async def pre_execute(
        self,
        node: ApiJobNode,
        execution: "TypedStatefulExecution"
    ) -> dict[str, Any]:
        """Pre-execute logic for ApiJobNode."""
        return {
            "url": node.url,
            "method": node.method.value if hasattr(node.method, 'value') else node.method,
            "headers": node.headers,
            "params": node.params,
            "body": node.body,
            "timeout": node.timeout,
            "auth_type": node.auth_type,
            "auth_config": node.auth_config
        }
    
    async def execute(
        self,
        node: ApiJobNode,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Use injected service or fall back to old pattern for backward compatibility
        api_service = self.api_service
        if not api_service:
            api_service = context.get_service("api_service")
            if not api_service:
                api_service = services.get("api_service")
            
        if not api_service:
            return self._build_output(
                {"default": ""}, 
                context,
                {"error": "API service not available"}
            )
        
        # Direct typed access to node properties
        url = node.url
        method = node.method
        headers = node.headers or {}
        params = node.params or {}
        body = node.body
        timeout = node.timeout or 30
        auth_type = node.auth_type or "none"
        auth_config = node.auth_config or {}

        if not url:
            return self._build_output(
                {"default": ""}, 
                context,
                {"error": "No URL provided"}
            )

        try:
            # Parse JSON strings for headers, params, body, and auth_config
            parsed_data = self._parse_json_inputs(headers, params, body, auth_config)
            if "error" in parsed_data:
                return self._build_output(
                    {"default": ""}, 
                    context,
                    {"error": parsed_data["error"]}
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
                max_retries=node.max_retries if hasattr(node, "max_retries") else 3,
                retry_delay=1.0,
                timeout=timeout,
                auth=auth,
                expected_status_codes=list(range(200, 300))  # 2xx status codes
            )
            
            # Format output
            output_value = json.dumps(response_data) if isinstance(response_data, dict) else str(response_data)
            
            return self._build_output(
                {"default": output_value},
                context,
                {
                    "success": True,
                    "url": url,
                    "method": method.value
                }
            )

        except Exception as e:
            # API service handles retries and specific errors
            # This catches any remaining errors
            return self._build_output(
                {"default": ""}, 
                context,
                {
                    "error": str(e),
                    "success": False,
                    "url": url,
                    "method": method.value
                }
            )

    def _parse_json_inputs(
        self, headers: Any, params: Any, body: Any, auth_config: Any
    ) -> dict[str, Any]:
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