
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.core.static.generated_nodes import EndpointNode
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.models import EndpointNodeData, NodeType

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
        return ["file_service"]

    @property
    def description(self) -> str:
        return "Endpoint node – pass through data and optionally save to file"

    def validate(self, request: ExecutionRequest[EndpointNode]) -> Optional[str]:
        """Validate the endpoint node configuration."""
        node = request.node
        
        # Validate file service is available if save_to_file is enabled
        if node.save_to_file:
            if not request.services.get("file_service") and not self.file_service:
                return "File service is required when save_to_file is enabled"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[EndpointNode]) -> NodeOutputProtocol:
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
        
        # Get service from services dict
        file_service = self.file_service or services.get("file_service")

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

                return DataOutput(
                    value={"default": result_data},
                    node_id=node.id,
                    metadata={"saved_to": file_name}
                )
            except Exception as exc:
                return DataOutput(
                    value={"default": result_data},
                    node_id=node.id,
                    metadata={"save_error": str(exc)}
                )

        return DataOutput(
            value={"default": result_data},
            node_id=node.id,
            metadata={}
        )
    
    def post_execute(
        self,
        request: ExecutionRequest[EndpointNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log endpoint execution."""
        # Log save details if in debug mode
        if request.metadata.get("debug") and request.metadata.get("save_config"):
            save_config = request.metadata["save_config"]
            print(f"[EndpointNode] Save configuration: {save_config}")
        
        return output