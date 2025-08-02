
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
    from dipeo.core.execution.execution_context import ExecutionContext
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
        node = request.node
        if node.save_to_file:
            if not request.get_service("filesystem_adapter") and not self.filesystem_adapter:
                return "Filesystem adapter is required when save_to_file is enabled"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[EndpointNode]) -> NodeOutputProtocol:
        node = request.node
        context = request.context
        inputs = request.inputs
        services = request.services
        if node.save_to_file:
            request.add_metadata("save_config", {
                "save": True,
                "filename": node.file_name or f"output_{node.id}.json"
            })
        
        if isinstance(services, dict):
            filesystem_adapter = self.filesystem_adapter or services.get("filesystem_adapter")
        else:
            from dipeo.application.registry import ServiceKey
            fs_key = ServiceKey("filesystem_adapter")
            filesystem_adapter = self.filesystem_adapter or services.get(fs_key)

        result_data = inputs if inputs else {}
        
        save_to_file = node.save_to_file
        file_name = node.file_name
        
        if not file_name and hasattr(node, 'metadata') and node.metadata:
            file_name = node.metadata.get('file_path')
        
        if not file_name:
            if isinstance(services, dict) and 'typed_node' in services:
                typed_node = services['typed_node']
                if hasattr(typed_node, 'to_dict'):
                    node_dict = typed_node.to_dict()
                    file_name = node_dict.get('file_path') or node_dict.get('file_name')
            elif hasattr(services, 'has') and hasattr(services, 'get'):
                from dipeo.application.registry import ServiceKey
                typed_node_key = ServiceKey("typed_node")
                if services.has(typed_node_key):
                    typed_node = services.get(typed_node_key)
                    if hasattr(typed_node, 'to_dict'):
                        node_dict = typed_node.to_dict()
                        file_name = node_dict.get('file_path') or node_dict.get('file_name')

        if save_to_file and file_name and filesystem_adapter:
            try:
                if isinstance(result_data, dict):
                    content = json.dumps(result_data, indent=2)
                else:
                    content = str(result_data)
                
                file_path = Path(file_name)
                parent_dir = file_path.parent
                if parent_dir != Path(".") and not filesystem_adapter.exists(parent_dir):
                    filesystem_adapter.mkdir(parent_dir, parents=True)
                
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
        if request.metadata.get("debug") and request.metadata.get("save_config"):
            save_config = request.metadata["save_config"]
            print(f"[EndpointNode] Save configuration: {save_config}")
        
        return output