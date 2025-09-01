"""Use case for loading and managing diagrams."""

import logging
import yaml
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


class DiagramLoadingUseCase:
    """Centralized use case for loading diagrams from various sources.
    
    This use case handles:
    - Constructing diagram file paths based on name and format
    - Loading diagrams from files
    - Loading diagrams from inline data
    - Format detection and conversion
    """
    
    FORMAT_MAP = {
        'light': '.light.yaml',
        'native': '.native.json',
        'readable': '.readable.yaml'
    }
    
    def __init__(self, diagram_service: Any = None):
        """Initialize the diagram loading use case.
        
        Args:
            diagram_service: Service for loading and converting diagrams
        """
        self._diagram_service = diagram_service
        self._diagram_cache: dict[str, Any] = {}
    
    def set_diagram_service(self, diagram_service: Any):
        """Set the diagram service for loading operations.
        
        Args:
            diagram_service: The diagram service to use
        """
        self._diagram_service = diagram_service
    
    def load_diagram(
        self,
        diagram_name: Optional[str] = None,
        diagram_format: Optional[str] = None,
        diagram_data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Load diagram from name/format or inline data.
        
        Args:
            diagram_name: Name/path of the diagram to load
            diagram_format: Format of the diagram (light, native, readable)
            diagram_data: Inline diagram data (if provided, name/format ignored)
            
        Returns:
            The loaded DomainDiagram object
            
        Raises:
            ValueError: If diagram cannot be loaded
        """
        # Load from inline data if provided
        if diagram_data:
            return self._load_from_data(diagram_data)
        
        # Load from file by name
        if diagram_name:
            return self._load_from_file(diagram_name, diagram_format)
        
        raise ValueError("No diagram specified for loading (neither name nor data)")
    
    def _load_from_data(self, diagram_data: Dict[str, Any]) -> Any:
        """Load diagram from inline data.
        
        Args:
            diagram_data: The inline diagram data
            
        Returns:
            The loaded DomainDiagram
            
        Raises:
            ValueError: If diagram service not available
        """
        if not self._diagram_service:
            raise ValueError("Diagram service not available for conversion")
        
        logger.debug("[DiagramLoading] Loading diagram from inline data")
        
        # Convert to YAML for processing
        yaml_content = yaml.dump(diagram_data, default_flow_style=False, sort_keys=False)
        return self._diagram_service.load_diagram(yaml_content)
    
    def _load_from_file(
        self,
        diagram_name: str,
        diagram_format: Optional[str] = None
    ) -> Any:
        """Load diagram from file.
        
        Args:
            diagram_name: Name/path of the diagram
            diagram_format: Format of the diagram
            
        Returns:
            The loaded DomainDiagram
            
        Raises:
            ValueError: If diagram cannot be loaded
        """
        if not self._diagram_service:
            raise ValueError("Diagram service not available")
        
        # Check cache first
        cache_key = f"{diagram_name}:{diagram_format or 'light'}"
        if cache_key in self._diagram_cache:
            logger.debug(f"[DiagramLoading] Using cached diagram: {cache_key}")
            return self._diagram_cache[cache_key]
        
        # Construct file path
        file_path = self.construct_diagram_path(diagram_name, diagram_format)
        
        try:
            logger.debug(f"[DiagramLoading] Loading diagram from: {file_path}")
            
            # Use diagram service to load the diagram
            diagram = self._diagram_service.load_from_file(file_path)
            
            # Cache the loaded diagram
            self._diagram_cache[cache_key] = diagram
            
            return diagram
            
        except Exception as e:
            logger.error(f"Error loading diagram from '{file_path}': {e!s}")
            raise ValueError(f"Failed to load diagram '{diagram_name}': {e!s}")
    
    def construct_diagram_path(
        self,
        diagram_name: str,
        diagram_format: Optional[str] = None
    ) -> str:
        """Construct the file path for a diagram.
        
        Path construction rules:
        - projects/* -> projects/{name}{suffix}
        - codegen/* -> files/codegen/{name}{suffix}
        - examples/* -> examples/{name}{suffix}
        - others -> examples/{name}{suffix}
        
        Args:
            diagram_name: Name/path of the diagram
            diagram_format: Format of the diagram (light, native, readable)
            
        Returns:
            The constructed file path for the diagram
        """
        # Determine format suffix
        format_suffix = self.FORMAT_MAP.get(
            diagram_format or 'light',
            '.light.yaml'
        )
        
        # Construct full file path based on prefix
        if diagram_name.startswith('projects/'):
            file_path = f"{diagram_name}{format_suffix}"
        elif diagram_name.startswith('codegen/'):
            file_path = f"files/{diagram_name}{format_suffix}"
        elif diagram_name.startswith('examples/'):
            file_path = f"{diagram_name}{format_suffix}"
        else:
            # Default to examples directory
            file_path = f"examples/{diagram_name}{format_suffix}"
        
        logger.debug(
            f"[DiagramLoading] Constructed path: {file_path} "
            f"for diagram: {diagram_name}, format: {diagram_format}"
        )
        
        return file_path
    
    def find_endpoint_outputs(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Find endpoint node outputs in execution results.
        
        Args:
            execution_results: The results from diagram execution
            
        Returns:
            A dictionary of endpoint outputs
        """
        return {
            k: v for k, v in execution_results.items()
            if k.startswith("endpoint") or k.startswith("end")
        }
    
    def process_output_mapping(
        self,
        execution_results: Dict[str, Any]
    ) -> Any:
        """Process output mapping from diagram execution results.
        
        Returns the appropriate output based on endpoint nodes or the last output.
        
        Args:
            execution_results: The results from the diagram execution
            
        Returns:
            The processed output value
        """
        if not execution_results:
            return {}
        
        # Find endpoint outputs
        endpoint_outputs = self.find_endpoint_outputs(execution_results)
        
        if endpoint_outputs:
            # If there's one endpoint, return its value directly
            if len(endpoint_outputs) == 1:
                return list(endpoint_outputs.values())[0]
            # Multiple endpoints, return all
            return endpoint_outputs
        
        # No endpoints, return the last output
        return list(execution_results.values())[-1] if execution_results else {}
    
    def clear_cache(self):
        """Clear the diagram cache."""
        self._diagram_cache.clear()
        logger.debug("[DiagramLoading] Diagram cache cleared")