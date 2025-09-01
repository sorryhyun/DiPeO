"""Base executor for sub-diagram execution with common functionality."""

import logging
import uuid
import yaml
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.use_cases import DiagramLoadingUseCase

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
        # Use case for diagram loading
        self._diagram_loading_use_case = DiagramLoadingUseCase()
    
    def set_services(self, **kwargs):
        """Set services for the executor to use.
        
        Subclasses can override to accept specific services.
        """
        self._state_store = kwargs.get('state_store')
        self._message_router = kwargs.get('message_router')
        self._diagram_service = kwargs.get('diagram_service')
        self._prepare_use_case = kwargs.get('prepare_use_case')
        # Set diagram service for the use case
        if self._diagram_service:
            self._diagram_loading_use_case.set_diagram_service(self._diagram_service)
    
    def _construct_diagram_path(self, node: "SubDiagramNode") -> str:
        """Construct the file path for a diagram.
        
        Args:
            node: The SubDiagramNode containing diagram information
            
        Returns:
            The constructed file path for the diagram
        """
        return self._diagram_loading_use_case.construct_diagram_path(
            node.diagram_name,
            node.diagram_format
        )
    
    def _process_output_mapping(self, node: "SubDiagramNode", execution_results: dict[str, Any]) -> Any:
        """Process output mapping from sub-diagram results.
        
        Returns the appropriate output based on endpoint nodes or the last output.
        
        Args:
            node: The SubDiagramNode being executed
            execution_results: The results from the sub-diagram execution
            
        Returns:
            The processed output value
        """
        return self._diagram_loading_use_case.process_output_mapping(execution_results)
    
    def _find_endpoint_outputs(self, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Find endpoint node outputs in execution results.
        
        Args:
            execution_results: The results from the sub-diagram execution
            
        Returns:
            A dictionary of endpoint outputs
        """
        return self._diagram_loading_use_case.find_endpoint_outputs(execution_results)
    
    async def _load_diagram(self, node: "SubDiagramNode") -> Any:
        """Load diagram as DomainDiagram.
        
        Args:
            node: The SubDiagramNode containing diagram information
            
        Returns:
            The loaded DomainDiagram
        """
        return self._diagram_loading_use_case.load_diagram(
            diagram_name=node.diagram_name,
            diagram_format=node.diagram_format,
            diagram_data=node.diagram_data
        )
    
    
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