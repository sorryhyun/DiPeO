
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path
import json

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.generated_nodes import EndpointNode, NodeType
from dipeo.core.execution.node_output import DataOutput, ErrorOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.endpoint_model import EndpointNodeData

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext
    from dipeo.domain.ports.storage import FileSystemPort


@register_handler
class EndpointNodeHandler(TypedNodeHandler[EndpointNode]):
    """
    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_request() - Core execution logic
    """
    
    def __init__(self, filesystem_adapter: Optional["FileSystemPort"] = None):
        self.filesystem_adapter = filesystem_adapter
        # Instance variables for passing data between methods
        self._current_save_enabled = False
        self._current_filename = None
        self._current_filesystem_adapter = None


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

    async def pre_execute(self, request: ExecutionRequest[EndpointNode]) -> Optional[NodeOutputProtocol]:
        """Pre-execution validation and setup."""
        node = request.node
        services = request.services
        
        # Check filesystem adapter availability if saving is enabled
        if node.save_to_file:
            filesystem_adapter = self.filesystem_adapter or services.resolve(FILESYSTEM_ADAPTER)
            
            if not filesystem_adapter:
                from dipeo.core.execution.node_output import ErrorOutput
                return ErrorOutput(
                    value="Filesystem adapter is required when save_to_file is enabled",
                    node_id=node.id,
                    error_type="ServiceNotAvailableError"
                )
            
            # Resolve file name
            file_name = node.file_name
            
            # Try to get file_name from metadata if not set
            if not file_name and hasattr(node, 'metadata') and node.metadata:
                file_name = node.metadata.get('file_path')
            
            # Try to get from typed_node service
            if not file_name:
                typed_node_key = ServiceKey("typed_node")
                if services.has(typed_node_key):
                    typed_node = services.get(typed_node_key)
                    if hasattr(typed_node, 'to_dict'):
                        node_dict = typed_node.to_dict()
                        file_name = node_dict.get('file_path') or node_dict.get('file_name')
            
            # Use default if still no file name
            if not file_name:
                file_name = f"output_{node.id}.json"
            
            # Store validated data in instance variables
            self._current_save_enabled = True
            self._current_filename = file_name
            self._current_filesystem_adapter = filesystem_adapter
        else:
            # Clear instance variables when not saving
            self._current_save_enabled = False
            self._current_filename = None
            self._current_filesystem_adapter = None
        
        # Return None to proceed with normal execution
        return None

    def validate(self, request: ExecutionRequest[EndpointNode]) -> Optional[str]:
        node = request.node
        if node.save_to_file:
            if not request.get_service("filesystem_adapter") and not self.filesystem_adapter:
                return "Filesystem adapter is required when save_to_file is enabled"
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[EndpointNode]) -> NodeOutputProtocol:
        """Pure execution using instance variables set in pre_execute."""
        node = request.node
        inputs = request.inputs
        
        result_data = inputs if inputs else {}
        
        # Check if we need to save to file (config prepared in pre_execute)
        if self._current_save_enabled:
            file_name = self._current_filename
            filesystem_adapter = self._current_filesystem_adapter
            
            if filesystem_adapter:
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
                        metadata=json.dumps({"saved_to": file_name})
                    )
                except Exception as exc:
                    # Return error when save fails
                    return ErrorOutput(
                        value=f"Failed to save to file {file_name}: {str(exc)}",
                        node_id=node.id,
                        error_type="SaveError",
                        metadata=json.dumps({"attempted_file": file_name})
                    )

        return DataOutput(
            value={"default": result_data},
            node_id=node.id,
            metadata="{}"
        )
    
    def post_execute(
        self,
        request: ExecutionRequest[EndpointNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        # Post-execution logging can use instance variables if needed
        # No need for metadata access
        return output