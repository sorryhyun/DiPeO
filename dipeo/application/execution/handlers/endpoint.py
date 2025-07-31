
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path
import json

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import EndpointNode, NodeType
from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.endpoint_model import EndpointNodeData

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext
    from dipeo.domain.ports.storage import FileSystemPort


@register_handler
class EndpointNodeHandler(TypedNodeHandler[EndpointNode]):
    
    def __init__(self, filesystem_adapter: Optional["FileSystemPort"] = None):
        self.filesystem_adapter = filesystem_adapter


    @property
    def node_class(self) -> type[EndpointNode]:
        return EndpointNode
    
    @property
    def node_type(self) -> str:
        return NodeType.ENDPOINT.value

    @property
    def schema(self) -> type[BaseModel]:
        return EndpointNodeData


    @property
    def requires_services(self) -> list[str]:
        return ["filesystem_adapter"]

    @property
    def description(self) -> str:
        return "Endpoint node – pass through data and optionally save to file"

    def validate(self, request: ExecutionRequest[EndpointNode]) -> Optional[str]:
        """Validate the endpoint node configuration."""
        node = request.node
        
        # Validate filesystem adapter is available if save_to_file is enabled
        if node.save_to_file:
            if not request.get_service("filesystem_adapter") and not self.filesystem_adapter:
                return "Filesystem adapter is required when save_to_file is enabled"
        
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
        
        # Get filesystem adapter (handle both dict and ServiceRegistry)
        if isinstance(services, dict):
            filesystem_adapter = self.filesystem_adapter or services.get("filesystem_adapter")
        else:
            # It's a ServiceRegistry
            from dipeo.application.registry import ServiceKey
            fs_key = ServiceKey("filesystem_adapter")
            filesystem_adapter = self.filesystem_adapter or services.get(fs_key)

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
        if not file_name:
            # Handle both dict and ServiceRegistry cases
            if isinstance(services, dict) and 'typed_node' in services:
                typed_node = services['typed_node']
                if hasattr(typed_node, 'to_dict'):
                    node_dict = typed_node.to_dict()
                    file_name = node_dict.get('file_path') or node_dict.get('file_name')
            elif hasattr(services, 'has') and hasattr(services, 'get'):
                # It's a ServiceRegistry
                from dipeo.application.registry import ServiceKey
                typed_node_key = ServiceKey("typed_node")
                if services.has(typed_node_key):
                    typed_node = services.get(typed_node_key)
                    if hasattr(typed_node, 'to_dict'):
                        node_dict = typed_node.to_dict()
                        file_name = node_dict.get('file_path') or node_dict.get('file_name')

        if save_to_file and file_name and filesystem_adapter:
            try:
                # Prepare content to save
                if isinstance(result_data, dict):
                    # Save as JSON for dict data
                    content = json.dumps(result_data, indent=2)
                else:
                    # Save as string for other types
                    content = str(result_data)
                
                # Convert to Path object
                file_path = Path(file_name)
                
                # Ensure parent directory exists
                parent_dir = file_path.parent
                if parent_dir != Path(".") and not filesystem_adapter.exists(parent_dir):
                    filesystem_adapter.mkdir(parent_dir, parents=True)
                
                # Write the file using FileSystemPort
                with filesystem_adapter.open(file_path, "wb") as f:
                    f.write(content.encode('utf-8'))

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