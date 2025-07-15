
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.types import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.service_key import FILE_SERVICE, ServiceKeyAdapter
from dipeo.core.static.generated_nodes import EndpointNode
from dipeo.models import EndpointNodeData, NodeOutput, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext


@register_handler
class EndpointNodeHandler(TypedNodeHandler[EndpointNode]):
    
    def __init__(self, file_service=None):
        self.file_service = file_service


    @property
    def node_class(self) -> type[EndpointNode]:
        return EndpointNode
    
    @property
    def node_type(self) -> str:
        return NodeType.endpoint.value

    @property
    def schema(self) -> type[BaseModel]:
        return EndpointNodeData


    @property
    def requires_services(self) -> list[str]:
        return ["file"]

    @property
    def description(self) -> str:
        return "Endpoint node – pass through data and optionally save to file"

    def validate(self, request: ExecutionRequest[EndpointNode]) -> Optional[str]:
        """Validate the endpoint node configuration."""
        node = request.node
        
        # Validate file service is available if save_to_file is enabled
        if node.save_to_file:
            service_adapter = ServiceKeyAdapter(request.services)
            if not service_adapter.has(FILE_SERVICE) and not self.file_service:
                return "File service is required when save_to_file is enabled"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[EndpointNode]) -> NodeOutput:
        """Execute the endpoint node."""
        node = request.node
        context = request.context
        inputs = request.inputs
        services = request.services
        # Store save configuration in metadata
        if node.save_to_file:
            request.add_metadata("save_config", {
                "save": True,
                "filename": node.file_name or f"output_{node.id}.json"
            })
        
        # Get service using ServiceKey
        service_adapter = ServiceKeyAdapter(services)
        file_service = self.file_service or service_adapter.get(FILE_SERVICE)
        if not file_service:
            file_service = context.get_service("file")  # Fallback for legacy compatibility

        # Endpoint nodes pass through their inputs
        result_data = inputs if inputs else {}
        
        # Direct typed access to node properties
        save_to_file = node.save_to_file
        # Handle both file_name and file_path from node data
        file_name = node.file_name
        
        # Also check the original node data for file_path if file_name is not set
        if not file_name and hasattr(node, 'metadata') and node.metadata:
            file_name = node.metadata.get('file_path')
        
        # Check in the raw node data from services
        if not file_name and 'typed_node' in services:
            typed_node = services['typed_node']
            if hasattr(typed_node, 'to_dict'):
                node_dict = typed_node.to_dict()
                file_name = node_dict.get('file_path') or node_dict.get('file_name')

        if save_to_file and file_name:
            try:
                if isinstance(result_data, dict) and "default" in result_data:
                    content = str(result_data["default"])
                else:
                    content = str(result_data)

                await file_service.write(file_name, None, None, content)

                return self._build_output(
                    {"default": result_data},
                    context,
                    {"saved_to": file_name}
                )
            except Exception as exc:
                return self._build_output(
                    {"default": result_data},
                    context,
                    {"save_error": str(exc)}
                )

        return self._build_output(
            {"default": result_data},
            context
        )
    
    def post_execute(
        self,
        request: ExecutionRequest[EndpointNode],
        output: NodeOutput
    ) -> NodeOutput:
        """Post-execution hook to log endpoint execution."""
        # Log save details if in debug mode
        if request.metadata.get("debug") and request.metadata.get("save_config"):
            save_config = request.metadata["save_config"]
            print(f"[EndpointNode] Save configuration: {save_config}")
        
        return output