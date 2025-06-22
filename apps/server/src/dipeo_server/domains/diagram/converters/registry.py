from typing import Dict, Optional, List, Tuple
from .base import DiagramConverter
from .unified_converter import UnifiedDiagramConverter
from dipeo_domain import DiagramFormat, DomainDiagram


class ConverterRegistry:
    
    def __init__(self):
        self._unified_converter = UnifiedDiagramConverter()
        self._initialize()
    
    def _initialize(self):
        pass
    
    def get(self, format_id: str) -> Optional[DiagramConverter]:
        if format_id in [s.format_id for s in self._unified_converter.strategies.values()]:
            self._unified_converter.set_format(format_id)
            return self._unified_converter
        return None
    
    def get_info(self, format_id: str) -> Optional[Dict[str, str]]:
        strategy = self._unified_converter.strategies.get(format_id)
        if strategy:
            return strategy.format_info
        return None
    
    def list_formats(self) -> List[Dict[str, str]]:
        return self._unified_converter.get_supported_formats()
    
    def detect_format(self, content: str) -> Optional[str]:
        return self._unified_converter.detect_format(content)
    
    def get_export_formats(self) -> List[Dict[str, str]]:
        return self._unified_converter.get_export_formats()
    
    def get_import_formats(self) -> List[Dict[str, str]]:
        return self._unified_converter.get_import_formats()
    
    def convert(self, content: str, from_format: str, to_format: str) -> str:
        diagram = self._unified_converter.deserialize(content, from_format)
        
        return self._unified_converter.serialize(diagram, to_format)
    
    def deserialize(self, content: str, format_id: Optional[str] = None) -> DomainDiagram:
        return self._unified_converter.deserialize(content, format_id)
    
    def serialize(self, diagram: DomainDiagram, format_id: str) -> str:
        return self._unified_converter.serialize(diagram, format_id)


converter_registry = ConverterRegistry()