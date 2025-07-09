"""Diagram Loader adapter implementation."""

from typing import Any, Dict, Optional, Union

from dipeo.core.ports import DiagramLoaderPort, FileServicePort
from dipeo.diagram import BackendDiagram, backend_to_graphql
from dipeo.diagram.unified_converter import UnifiedDiagramConverter
from dipeo.models import DiagramFormat, DomainDiagram


class DiagramLoaderAdapter:
    """Infrastructure adapter for diagram loading and format detection."""
    
    def __init__(self, file_service: FileServicePort):
        """Initialize the adapter.
        
        Args:
            file_service: File service for reading diagram files
        """
        self.file_service = file_service
        self.converter = UnifiedDiagramConverter()
    
    def detect_format(self, content: str) -> DiagramFormat:
        """Detect the format of diagram content.
        
        Args:
            content: Raw content to analyze
            
        Returns:
            Detected diagram format
            
        Raises:
            ValueError: If format cannot be detected
        """
        content = content.strip()
        
        # Try JSON detection
        if content.startswith('{'):
            import json
            try:
                data = json.loads(content)
                # Check for native format indicators
                if "nodes" in data and isinstance(data["nodes"], dict):
                    return DiagramFormat.native
                return DiagramFormat.native
            except json.JSONDecodeError:
                pass
        
        # Try YAML detection
        try:
            import yaml
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                # Check for light format indicators
                if (data.get("version") == "light" or 
                    (isinstance(data.get("nodes"), list) and 
                     "connections" in data and 
                     "persons" in data)):
                    return DiagramFormat.light
                # Check for readable format
                if data.get("format") == "readable":
                    return DiagramFormat.readable
                # Default YAML is light format
                return DiagramFormat.light
        except yaml.YAMLError:
            pass
        
        raise ValueError("Unable to detect diagram format")
    
    def load_diagram(
        self,
        content: str,
        format: Optional[DiagramFormat] = None,
    ) -> DomainDiagram:
        """Load a diagram from content.
        
        Args:
            content: Raw content to parse
            format: Optional format hint. If not provided, will auto-detect
            
        Returns:
            Parsed diagram object
            
        Raises:
            ValueError: If diagram cannot be parsed
        """
        if format is None:
            format = self.detect_format(content)
        
        # Use the unified converter for deserialization
        return self.converter.deserialize(content, format_id=format.value)
    
    async def load_from_file(
        self,
        file_path: str,
        format: Optional[DiagramFormat] = None,
    ) -> DomainDiagram:
        """Load a diagram from a file.
        
        Args:
            file_path: Path to the diagram file
            format: Optional format hint. If not provided, will auto-detect
            
        Returns:
            Parsed diagram object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If diagram cannot be parsed
        """
        # Read file using file service
        result = self.file_service.read(file_path)
        content = result.get("content", "")
        
        if not content:
            raise ValueError(f"Empty or missing content in file: {file_path}")
        
        return self.load_diagram(content, format)
    
    def prepare_diagram(
        self,
        diagram_ref: Union[str, Dict[str, Any], DomainDiagram],
    ) -> DomainDiagram:
        """Prepare a diagram from various input types.
        
        Args:
            diagram_ref: Can be:
                - A file path (string)
                - A diagram dict
                - A Diagram object
                
        Returns:
            Prepared diagram object
            
        Raises:
            ValueError: If diagram cannot be prepared
        """
        import yaml
        
        # If it's already a DomainDiagram object, validate and return
        if isinstance(diagram_ref, DomainDiagram):
            return diagram_ref
        
        # If it's a string, assume it's a file path
        if isinstance(diagram_ref, str):
            # This will be handled by load_from_file in async contexts
            raise ValueError("File paths should be loaded using load_from_file")
        
        # If it's a dictionary, process it
        if isinstance(diagram_ref, dict):
            # Check if diagram is in backend format (dict of dicts)
            if isinstance(diagram_ref.get("nodes"), dict):
                # Convert from backend format to domain format
                backend_diagram = BackendDiagram(**diagram_ref)
                return backend_to_graphql(backend_diagram)
            
            # Check if this is light format
            if (diagram_ref.get("version") == "light" or 
                (isinstance(diagram_ref.get("nodes"), list) and 
                 "connections" in diagram_ref and 
                 "persons" in diagram_ref)):
                # This is light format - convert to YAML string then deserialize
                content = yaml.dump(diagram_ref, default_flow_style=False, sort_keys=False)
                return self.converter.deserialize(content, format_id="light")
            
            # Assume it's already in domain format, validate directly
            return DomainDiagram.model_validate(diagram_ref)
        
        raise ValueError(f"Unsupported diagram reference type: {type(diagram_ref)}")