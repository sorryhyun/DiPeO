"""Base executor for sub-diagram execution with common functionality."""

import logging
import uuid
import yaml
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo.diagram_generated.generated_nodes import SubDiagramNode

logger = logging.getLogger(__name__)


class BaseSubDiagramExecutor:
    """Base class for sub-diagram executors with common functionality."""
    
    def __init__(self):
        """Initialize base executor."""
        # Services that may be used by subclasses
        self._state_store = None
        self._message_router = None
        self._diagram_service = None
        self._prepare_use_case = None
    
    def set_services(self, **kwargs):
        """Set services for the executor to use.
        
        Subclasses can override to accept specific services.
        """
        self._state_store = kwargs.get('state_store')
        self._message_router = kwargs.get('message_router')
        self._diagram_service = kwargs.get('diagram_service')
        self._prepare_use_case = kwargs.get('prepare_use_case')
    
    def _construct_diagram_path(self, node: "SubDiagramNode") -> str:
        """Construct the file path for a diagram.
        
        Args:
            node: The SubDiagramNode containing diagram information
            
        Returns:
            The constructed file path for the diagram
        """
        diagram_name = node.diagram_name
        
        # Determine format suffix
        format_suffix = ".light.yaml"  # Default format
        if node.diagram_format:
            format_map = {
                'light': '.light.yaml',
                'native': '.native.json',
                'readable': '.readable.yaml'
            }
            format_suffix = format_map.get(node.diagram_format, '.light.yaml')
        
        # Construct full file path
        if diagram_name.startswith('projects/'):
            return f"{diagram_name}{format_suffix}"
        elif diagram_name.startswith('codegen/'):
            return f"files/{diagram_name}{format_suffix}"
        elif diagram_name.startswith('examples/'):
            return f"{diagram_name}{format_suffix}"
        else:
            return f"examples/{diagram_name}{format_suffix}"
    
    def _process_output_mapping(self, node: "SubDiagramNode", execution_results: dict[str, Any]) -> Any:
        """Process output mapping from sub-diagram results.
        
        Returns the appropriate output based on endpoint nodes or the last output.
        
        Args:
            node: The SubDiagramNode being executed
            execution_results: The results from the sub-diagram execution
            
        Returns:
            The processed output value
        """
        if not execution_results:
            return {}
        
        # Find endpoint outputs
        endpoint_outputs = self._find_endpoint_outputs(execution_results)
        
        if endpoint_outputs:
            # If there's one endpoint, return its value directly
            if len(endpoint_outputs) == 1:
                return list(endpoint_outputs.values())[0]
            # Multiple endpoints, return all
            return endpoint_outputs
        
        # No endpoints, return the last output
        return list(execution_results.values())[-1] if execution_results else {}
    
    def _find_endpoint_outputs(self, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Find endpoint node outputs in execution results.
        
        Args:
            execution_results: The results from the sub-diagram execution
            
        Returns:
            A dictionary of endpoint outputs
        """
        return {
            k: v for k, v in execution_results.items() 
            if k.startswith("endpoint") or k.startswith("end")
        }
    
    async def _load_diagram(self, node: "SubDiagramNode") -> Any:
        """Load diagram as DomainDiagram.
        
        Args:
            node: The SubDiagramNode containing diagram information
            
        Returns:
            The loaded DomainDiagram
        """
        # If diagram_data is provided directly, convert it to DomainDiagram
        if node.diagram_data:
            return await self._load_diagram_from_data(node.diagram_data)
        
        # Otherwise, load by name from storage
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
        return await self._load_diagram_from_file(node)
    
    async def _load_diagram_from_data(self, diagram_data: dict[str, Any]) -> Any:
        """Load diagram from inline data.
        
        Args:
            diagram_data: The inline diagram data
            
        Returns:
            The loaded DomainDiagram
        """
        if not self._diagram_service:
            raise ValueError("Diagram service not available for conversion")
        
        yaml_content = yaml.dump(diagram_data, default_flow_style=False, sort_keys=False)
        return self._diagram_service.load_diagram(yaml_content)
    
    async def _load_diagram_from_file(self, node: "SubDiagramNode") -> Any:
        """Load diagram from file.
        
        Args:
            node: The SubDiagramNode containing diagram information
            
        Returns:
            The loaded DomainDiagram
        """
        if not self._diagram_service:
            raise ValueError("Diagram service not available")
        
        # Construct file path based on diagram name and format
        file_path = self._construct_diagram_path(node)
        
        try:
            # Use diagram service to load the diagram - returns DomainDiagram
            diagram = await self._diagram_service.load_from_file(file_path)
            return diagram
        except Exception as e:
            logger.error(f"Error loading diagram from '{file_path}': {e!s}")
            raise ValueError(f"Failed to load diagram '{node.diagram_name}': {e!s}")
    
    def _create_execution_id(self, parent_execution_id: str, suffix: str = "sub") -> str:
        """Create a unique execution ID for sub-diagram.
        
        Args:
            parent_execution_id: The parent execution ID
            suffix: The suffix to use for the execution ID
            
        Returns:
            A unique execution ID
        """
        return f"{parent_execution_id}_{suffix}_{uuid.uuid4().hex[:8]}"
    
    def _format_error_output(self, node: "SubDiagramNode", error: Any, **metadata) -> dict[str, Any]:
        """Format an error output response.
        
        Args:
            node: The SubDiagramNode that failed
            error: The error that occurred
            **metadata: Additional metadata to include
            
        Returns:
            A formatted error output
        """
        error_data = {"error": str(error)}
        error_data.update(metadata)
        return error_data