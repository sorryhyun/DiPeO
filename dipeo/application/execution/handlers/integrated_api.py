"""Handler for Integrated API node."""

import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import INTEGRATED_API_SERVICE, API_KEY_SERVICE
from dipeo.diagram_generated.generated_nodes import IntegratedApiNode, NodeType
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.integrated_api_model import IntegratedApiNodeData
from dipeo.diagram_generated.enums import APIServiceType

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext


@register_handler
class IntegratedApiNodeHandler(TypedNodeHandler[IntegratedApiNode]):
    """Handler for executing integrated API operations across multiple providers."""
    
    def __init__(self, integrated_api_service=None, api_key_service=None):
        self.integrated_api_service = integrated_api_service
        self.api_key_service = api_key_service

    @property
    def node_class(self) -> type[IntegratedApiNode]:
        return IntegratedApiNode
    
    @property
    def node_type(self) -> str:
        return NodeType.INTEGRATED_API.value

    @property
    def schema(self) -> type[BaseModel]:
        return IntegratedApiNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["integrated_api_service", "api_key_service"]

    @property
    def description(self) -> str:
        return "Executes operations on various API providers (Notion, Slack, GitHub, etc.)"

    async def execute_request(self, request: ExecutionRequest[IntegratedApiNode]) -> NodeOutputProtocol:
        return await self._execute_api_operation(request)
    
    async def _execute_api_operation(self, request: ExecutionRequest[IntegratedApiNode]) -> NodeOutputProtocol:
        """Execute the API operation through the integrated service."""
        
        # Extract properties from request
        node = request.node
        context = request.context
        inputs = request.inputs
        
        # Get services from ServiceRegistry
        integrated_api_service = self.integrated_api_service or request.services.resolve(INTEGRATED_API_SERVICE)
        api_key_service = self.api_key_service or request.services.resolve(API_KEY_SERVICE)
        
        if not integrated_api_service:
            return ErrorOutput(
                value="Integrated API service not available",
                node_id=node.id,
                error_type="ServiceNotAvailableError"
            )
        
        if not api_key_service:
            return ErrorOutput(
                value="API key service not available",
                node_id=node.id,
                error_type="ServiceNotAvailableError"
            )
        
        # Get the API key for the provider
        provider = node.provider
        operation = node.operation
        
        # Handle enum values
        if hasattr(provider, 'value'):
            provider = provider.value
        
        # Get API key from the key service
        # First find the key ID for this provider
        api_keys = api_key_service.list_api_keys()
        provider_summary = next(
            (k for k in api_keys if k["service"] == provider), 
            None
        )
        
        if not provider_summary:
            return ErrorOutput(
                value=f"No API key configured for provider '{provider}'",
                node_id=node.id,
                error_type="ConfigurationError"
            )
        
        # Now get the full key details including the actual key
        provider_key = api_key_service.get_api_key(provider_summary["id"])
        api_key = provider_key["key"]
        
        # Prepare configuration
        config = node.config or {}
        
        # Merge any input data into config
        if inputs:
            # Handle different input structures
            default_input = inputs.get("default", {})
            if isinstance(default_input, dict):
                config = {**config, **default_input}
            elif default_input:
                # If input is not a dict, add it as a 'data' field
                config["data"] = default_input
        
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
            "max_retries": max_retries
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
                max_retries=max_retries
            )
            
            # Successfully executed operation
            
            return DataOutput(
                value={"default": result},
                node_id=node.id,
                metadata=json.dumps({
                    "provider": provider,
                    "operation": operation,
                    "success": True
                })
            )
            
        except ValueError as e:
            # Configuration or validation errors
            # Validation error
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type="ValidationError",
                metadata=json.dumps({
                    "provider": provider,
                    "operation": operation
                })
            )
            
        except Exception as e:
            # Other errors
            # API operation failed
            return ErrorOutput(
                value=str(e),
                node_id=node.id,
                error_type=type(e).__name__,
                metadata=json.dumps({
                    "provider": provider,
                    "operation": operation
                })
            )