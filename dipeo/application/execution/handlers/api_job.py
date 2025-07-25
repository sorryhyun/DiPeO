
import json
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.unified_service_registry import API_SERVICE
from dipeo.diagram_generated.nodes.api_job_node import ApiJobNode
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol
from dipeo.diagram_generated import ApiJobNodeData, HttpMethod, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


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

    async def execute_request(self, request: ExecutionRequest[ApiJobNode]) -> NodeOutputProtocol:
        """Execute the API request."""
        node = request.node
        context = request.context
        inputs = request.inputs
        services = request.services
        # Use injected service or get from services
        api_service = self.api_service or services.get(API_SERVICE.name)
            
        if not api_service:
            return ErrorOutput(
                value="API service not available",
                node_id=node.id,
                error_type="ServiceNotAvailableError"
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
        
        # Debug logging
        print(f"[ApiJobNode] URL: {url}")
        print(f"[ApiJobNode] Method type: {type(method)}, value: {method}")
        print(f"[ApiJobNode] Headers: {headers}")
        
        # Convert method to HttpMethod if it's a string
        if isinstance(method, str):
            try:
                method = HttpMethod(method.upper())
            except ValueError:
                return ErrorOutput(
                    value=f"Invalid HTTP method: {method}",
                    node_id=node.id,
                    error_type="ValidationError"
                )

        if not url:
            return ErrorOutput(
                value="No URL provided",
                node_id=node.id,
                error_type="ValidationError"
            )

        try:
            # Parse JSON strings for headers, params, body, and auth_config
            parsed_data = self._parse_json_inputs(headers, params, body, auth_config)
            if "error" in parsed_data:
                return ErrorOutput(
                    value=parsed_data["error"],
                    node_id=node.id,
                    error_type="ValidationError"
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
            # Get method value - handle both enum and string cases
            method_value = method.value if hasattr(method, 'value') else str(method)
            
            response_data = await api_service.execute_with_retry(
                url=url,
                method=method_value,
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
            
            return TextOutput(
                value=output_value,
                node_id=node.id,
                metadata={
                    "success": True,
                    "url": url,
                    "method": method_value
                }
            )

        except Exception as e:
            # API service handles retries and specific errors
            # This catches any remaining errors
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__,
                metadata={
                    "url": url,
                    "method": method.value if hasattr(method, 'value') else str(method)
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
    
    def post_execute(
        self,
        request: ExecutionRequest[ApiJobNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log API request details."""
        # Log API call details if in debug mode
        if request.metadata.get("debug"):
            method = request.metadata.get("method", "unknown")
            url = request.metadata.get("url", "unknown")
            success = output.metadata.get("success", False)
            print(f"[ApiJobNode] {method} {url} - Success: {success}")
            if not success and output.metadata.get("error"):
                print(f"[ApiJobNode] Error: {output.metadata['error']}")
        
        return output
    
    async def on_error(
        self,
        request: ExecutionRequest[ApiJobNode],
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        """Handle API errors with better error messages."""
        url = request.metadata.get("url", "unknown")
        method = request.metadata.get("method", "unknown")
        
        # Create error output with request information
        return ErrorOutput(
            value=f"API request failed: {str(error)}",
            node_id=request.node.id,
            error_type=type(error).__name__,
            metadata={
                "url": url,
                "method": method
            }
        )