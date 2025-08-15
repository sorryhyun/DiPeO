
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path
import json

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.generated_nodes import EndpointNode, NodeType
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
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
    3. execute_with_envelopes() - Core execution logic with envelope inputs
    
    Now uses envelope-based communication for clean input/output interfaces.
    """
    
    def __init__(self, filesystem_adapter: Optional["FileSystemPort"] = None):
        super().__init__()
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

    async def pre_execute(self, request: ExecutionRequest[EndpointNode]) -> Optional[Envelope]:
        """Pre-execution validation and setup."""
        node = request.node
        services = request.services
        
        # Check filesystem adapter availability if saving is enabled
        if node.save_to_file:
            filesystem_adapter = self.filesystem_adapter or services.resolve(FILESYSTEM_ADAPTER)
            
            if not filesystem_adapter:
                return EnvelopeFactory.error(
                    "Filesystem adapter is required when save_to_file is enabled",
                    error_type="ValueError",
                    produced_by=str(node.id)
                )
            
            # Resolve file name
            file_name = node.file_name
            
            # Try to get file_name from metadata if not set
            if not file_name and hasattr(node, 'metadata') and node.metadata:
                file_name = node.metadata.get('file_path')
            
            # Try to get from node config if available
            if not file_name:
                # Use node.id as a default fallback
                pass
            
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
    
    async def execute_with_envelopes(
        self, 
        request: ExecutionRequest[EndpointNode],
        inputs: dict[str, Envelope]
    ) -> Envelope:
        """Execute endpoint with envelope inputs."""
        node = request.node
        trace_id = request.execution_id or ""
        
        # Convert envelope inputs to data
        result_data = {}
        for key, envelope in inputs.items():
            try:
                # Try to parse as JSON first
                result_data[key] = envelope.as_json()
            except ValueError:
                # Fall back to text
                result_data[key] = envelope.as_text()
        
        # If only one input with key 'default', unwrap it
        if len(result_data) == 1 and 'default' in result_data:
            result_data = result_data['default']
        
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

                    # Create output envelope
                    output_envelope = EnvelopeFactory.json(
                        result_data if isinstance(result_data, dict) else {"default": result_data},
                        produced_by=node.id,
                        trace_id=trace_id
                    ).with_meta(
                        saved_to=file_name
                    )
                    
                    return output_envelope
                except Exception as exc:
                    # Return error when save fails
                    error_envelope = EnvelopeFactory.text(
                        f"Failed to save to file {file_name}: {str(exc)}",
                        produced_by=node.id,
                        trace_id=trace_id
                    ).with_meta(
                        error_type="SaveError",
                        attempted_file=file_name
                    )
                    return EnvelopeFactory.error(
                        str(exc),
                        error_type=exc.__class__.__name__,
                        produced_by=str(node.id),
                        trace_id=trace_id
                    )

        # Create output envelope for pass-through case
        output_envelope = EnvelopeFactory.json(
            result_data if isinstance(result_data, dict) else {"default": result_data},
            produced_by=node.id,
            trace_id=trace_id
        )
        
        return output_envelope
    
    def post_execute(
        self,
        request: ExecutionRequest[EndpointNode],
        output: Envelope
    ) -> Envelope:
        # Post-execution logging can use instance variables if needed
        # No need for metadata access
        return output