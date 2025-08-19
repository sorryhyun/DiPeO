
from typing import TYPE_CHECKING, Any, Optional
from pathlib import Path
import json

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry.keys import FILESYSTEM_ADAPTER
from dipeo.diagram_generated.generated_nodes import EndpointNode, NodeType
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.endpoint_model import EndpointNodeData

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext
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
    
    def __init__(self):
        super().__init__()
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
            filesystem_adapter = services.resolve(FILESYSTEM_ADAPTER)
            
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
            if not request.get_service(FILESYSTEM_ADAPTER):
                return "Filesystem adapter is required when save_to_file is enabled"
        
        return None
    
    async def prepare_inputs(
        self,
        request: ExecutionRequest[EndpointNode],
        inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to data."""
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
        
        return {"data": result_data}
    
    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[EndpointNode]
    ) -> Any:
        """Execute endpoint logic."""
        node = request.node
        
        # Get data from prepared inputs
        result_data = inputs.get("data", {})
        
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

                    # Return data with save metadata
                    return {
                        "data": result_data,
                        "saved_to": file_name,
                        "save_success": True
                    }
                except Exception as exc:
                    # Return error when save fails
                    raise Exception(f"Failed to save to file {file_name}: {str(exc)}")

        # Return data for pass-through case
        return {
            "data": result_data,
            "saved_to": None,
            "save_success": False
        }
    
    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[EndpointNode]
    ) -> Envelope:
        """Serialize endpoint result to envelope."""
        node = request.node
        trace_id = request.execution_id or ""
        
        # Extract data and metadata from result
        result_data = result.get("data", {})
        saved_to = result.get("saved_to")
        
        # Create output envelope
        output_envelope = EnvelopeFactory.json(
            result_data if isinstance(result_data, dict) else {"default": result_data},
            produced_by=node.id,
            trace_id=trace_id
        )
        
        # Add save metadata if applicable
        if saved_to:
            output_envelope = output_envelope.with_meta(
                saved_to=saved_to
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