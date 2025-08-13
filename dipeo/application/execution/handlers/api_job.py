
import json
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry import API_SERVICE
from dipeo.diagram_generated.generated_nodes import ApiJobNode, NodeType
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, NodeOutputProtocol, APIJobOutput
from dipeo.diagram_generated.models.api_job_model import ApiJobNodeData, HttpMethod

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class ApiJobNodeHandler(TypedNodeHandler[ApiJobNode]):
    """
    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_request() - Core execution logic
    """
    
    def __init__(self, api_service=None):
        self.api_service = api_service
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
        return ApiJobNodeData
    

    @property
    def requires_services(self) -> list[str]:
        return ["api_service"]

    @property
    def description(self) -> str:
        return "Makes HTTP requests to external APIs with authentication support"

    async def pre_execute(self, request: ExecutionRequest[ApiJobNode]) -> Optional[NodeOutputProtocol]:
        """Pre-execution validation and setup."""
        node = request.node
        
        # Check service availability
        api_service = self.api_service or request.get_service(API_SERVICE.name)
        if not api_service:
            return ErrorOutput(
                value="API service not available",
                node_id=node.id,
                error_type="ServiceNotAvailableError"
            )
        
        # Validate URL
        if not node.url:
            return ErrorOutput(
                value="No URL provided",
                node_id=node.id,
                error_type="ValidationError"
            )
        
        # Convert and validate HTTP method
        method = node.method
        if isinstance(method, str):
            try:
                method = HttpMethod(method.upper())
            except ValueError:
                return ErrorOutput(
                    value=f"Invalid HTTP method: {method}",
                    node_id=node.id,
                    error_type="ValidationError"
                )
        
        # Parse and validate JSON inputs
        headers = node.headers or {}
        params = node.params or {}
        body = node.body
        auth_config = node.auth_config or {}
        
        parsed_data = self._parse_json_inputs(headers, params, body, auth_config)
        if "error" in parsed_data:
            return ErrorOutput(
                value=parsed_data["error"],
                node_id=node.id,
                error_type="ValidationError"
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

    async def execute_request(self, request: ExecutionRequest[ApiJobNode]) -> NodeOutputProtocol:
        """Pure execution using instance variables set in pre_execute."""
        node = request.node
        
        # Use pre-validated data from instance variables (set in pre_execute)
        api_service = self._current_api_service
        method = self._current_method
        headers = self._current_headers
        params = self._current_params
        body = self._current_body
        auth_config = self._current_auth_config
        
        # Get additional node configuration
        url = node.url
        timeout = node.timeout or 30
        auth_type = node.auth_type or "none"
        
        print(f"[ApiJobNode] URL: {url}")
        print(f"[ApiJobNode] Method: {method}")
        print(f"[ApiJobNode] Headers: {headers}")

        try:

            auth = self._prepare_auth(auth_type, auth_config)
            headers = self._apply_auth_headers(headers, auth_type, auth_config)
            request_data = self._prepare_request_data(method, params, body)
            
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
                expected_status_codes=list(range(200, 300))
            )
            
            # Convert response to dict format for APIJobOutput
            response_dict = response_data if isinstance(response_data, dict) else {"result": str(response_data)}
            
            # Note: In a real implementation, we'd get status_code and headers from the actual HTTP response
            # For now, we'll use defaults since the api_service abstraction doesn't provide these
            return APIJobOutput(
                value=response_dict,
                node_id=node.id,
                status_code=200,  # Default success code
                headers={},  # Would be populated from actual response
                metadata="{}",  # Empty metadata - url and method are now typed fields
                url=url,  # Use typed field
                method=method_value  # Use typed field
            )

        except Exception as e:
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__,
                metadata="{}"  # Empty metadata - error details in value and error_type
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
            try:
                result["body"] = json.loads(body)
            except json.JSONDecodeError:
                pass
        
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
    
    def post_execute(
        self,
        request: ExecutionRequest[ApiJobNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        # Post-execution logging can use node properties or output fields
        # No need for metadata access
        return output
    
    async def on_error(
        self,
        request: ExecutionRequest[ApiJobNode],
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        # Use node properties for error context
        url = request.node.url or "unknown"
        method = str(self._current_method) if self._current_method else request.node.method or "unknown"
        
        output = ErrorOutput(
            value=f"API request failed: {str(error)}",
            node_id=request.node.id,
            error_type=type(error).__name__
        )
        output.metadata = json.dumps({
            "url": url,
            "method": method
        })
        return output