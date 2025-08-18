"""Use case for serializing and deserializing diagrams."""

from typing import Optional

from dipeo.diagram_generated import DomainDiagram, DiagramFormat
from dipeo.domain.diagram.ports import DiagramStorageSerializer


class SerializeDiagramUseCase:
    """Use case for diagram serialization/deserialization.
    
    This use case handles:
    - Serializing diagrams to various formats (JSON, YAML, light, readable)
    - Deserializing string content to domain diagrams
    - Format detection and conversion
    """
    
    def __init__(self, diagram_serializer: DiagramStorageSerializer):
        """Initialize the use case with required dependencies.
        
        Args:
            diagram_serializer: Serializer for diagram conversion
        """
        self.diagram_serializer = diagram_serializer
    
    def serialize(
        self, 
        diagram: DomainDiagram, 
        format: str = "json"
    ) -> str:
        """Serialize a domain diagram to string format.
        
        Args:
            diagram: The diagram to serialize
            format: Target format ('json', 'yaml', 'light', 'readable')
            
        Returns:
            String representation of the diagram
        """
        return self.diagram_serializer.serialize_for_storage(diagram, format)
    
    def deserialize(
        self, 
        content: str, 
        format: Optional[str] = None
    ) -> DomainDiagram:
        """Deserialize string content to a domain diagram.
        
        Args:
            content: String content to deserialize
            format: Optional format hint, auto-detects if not provided
            
        Returns:
            DomainDiagram instance
        """
        return self.diagram_serializer.deserialize_from_storage(content, format)
    
    def convert_format(
        self,
        content: str,
        target_format: str,
        source_format: Optional[str] = None
    ) -> str:
        """Convert diagram content from one format to another.
        
        Args:
            content: Source content to convert
            target_format: Target format for conversion
            source_format: Optional source format, auto-detects if not provided
            
        Returns:
            Converted string in target format
        """
        # Deserialize from source format
        diagram = self.deserialize(content, source_format)
        
        # Serialize to target format
        return self.serialize(diagram, target_format)
    
    def validate_content(
        self,
        content: str,
        format: Optional[str] = None
    ) -> tuple[bool, list[str]]:
        """Validate that content can be deserialized.
        
        Args:
            content: Content to validate
            format: Optional format hint
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        return self.diagram_serializer.validate(content)
    
    def serialize_to_formats(
        self,
        diagram: DomainDiagram,
        formats: list[str]
    ) -> dict[str, str]:
        """Serialize a diagram to multiple formats.
        
        Args:
            diagram: The diagram to serialize
            formats: List of target formats
            
        Returns:
            Dictionary mapping format to serialized content
        """
        results = {}
        for format in formats:
            try:
                results[format] = self.serialize(diagram, format)
            except Exception as e:
                results[format] = f"Error: {str(e)}"
        return results
    
    def get_supported_formats(self) -> list[str]:
        """Get list of supported serialization formats.
        
        Returns:
            List of format names
        """
        return ["json", "yaml", "light", "readable"]
    
    def detect_format(self, content: str) -> Optional[str]:
        """Detect the format of diagram content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Detected format name or None if unknown
        """
        # Try to detect based on content structure
        content = content.strip()
        
        # JSON detection
        if content.startswith('{') or content.startswith('['):
            try:
                import json
                json.loads(content)
                # Check if it's light format (has specific structure)
                data = json.loads(content)
                if isinstance(data, dict):
                    if "nodes" in data and isinstance(data.get("nodes"), list):
                        # Check for light format markers
                        if any(isinstance(node, dict) and "type" in node 
                               for node in data["nodes"]):
                            return "light"
                        return "json"
            except:
                pass
        
        # YAML detection
        if not content.startswith('{'):
            try:
                import yaml
                data = yaml.safe_load(content)
                if isinstance(data, dict) and "nodes" in data:
                    return "yaml"
            except:
                pass
        
        return None