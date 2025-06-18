"""Converter registry for managing diagram format converters."""
from typing import Dict, Optional, List, Tuple
from .base import DiagramConverter
from .unified_converter import UnifiedDiagramConverter
from ..models.domain import DiagramFormat, DomainDiagram


class ConverterRegistry:
    """Registry for diagram format converters using unified converter."""
    
    def __init__(self):
        # Use a single unified converter instance
        self._unified_converter = UnifiedDiagramConverter()
        self._initialize()
    
    def _initialize(self):
        """Initialize the registry (strategies are auto-registered in UnifiedDiagramConverter)."""
        # The unified converter already has all strategies registered
        pass
    
    def get(self, format_id: str) -> Optional[DiagramConverter]:
        """Get converter by format ID."""
        # Check if format exists
        if format_id in [s.format_id for s in self._unified_converter.strategies.values()]:
            # Set the active format on the unified converter
            self._unified_converter.set_format(format_id)
            return self._unified_converter
        return None
    
    def get_info(self, format_id: str) -> Optional[Dict[str, str]]:
        """Get format metadata."""
        strategy = self._unified_converter.strategies.get(format_id)
        if strategy:
            return strategy.format_info
        return None
    
    def list_formats(self) -> List[Dict[str, str]]:
        """List all registered formats with their info."""
        return self._unified_converter.get_supported_formats()
    
    def detect_format(self, content: str) -> Optional[str]:
        """
        Automatically detect format from content.
        Returns the format ID with highest confidence.
        """
        return self._unified_converter.detect_format(content)
    
    def get_export_formats(self) -> List[Dict[str, str]]:
        """Get formats that support export."""
        return self._unified_converter.get_export_formats()
    
    def get_import_formats(self) -> List[Dict[str, str]]:
        """Get formats that support import."""
        return self._unified_converter.get_import_formats()
    
    def convert(self, content: str, from_format: str, to_format: str) -> str:
        """Convert content from one format to another."""
        # Deserialize from source format
        diagram = self._unified_converter.deserialize(content, from_format)
        
        # Serialize to target format
        return self._unified_converter.serialize(diagram, to_format)
    
    def deserialize(self, content: str, format_id: Optional[str] = None) -> DomainDiagram:
        """Deserialize content to domain diagram."""
        return self._unified_converter.deserialize(content, format_id)
    
    def serialize(self, diagram: DomainDiagram, format_id: str) -> str:
        """Serialize domain diagram to format."""
        return self._unified_converter.serialize(diagram, format_id)


# Global registry instance
converter_registry = ConverterRegistry()