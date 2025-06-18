"""Converter registry for managing diagram format converters."""
from typing import Dict, Optional, List, Tuple
from .base import DiagramConverter
from .domain_json import DomainJsonConverter
from .light_yaml import LightYamlConverter
from .readable_yaml import ReadableYamlConverter
from ..models.domain import DiagramFormat


class ConverterRegistry:
    """Registry for diagram format converters."""
    
    def __init__(self):
        self._converters: Dict[str, DiagramConverter] = {}
        self._format_info: Dict[str, Dict[str, str]] = {}
        self._initialize_default_converters()
    
    def _initialize_default_converters(self):
        """Register default converters."""
        # Domain JSON
        self.register(
            DiagramFormat.NATIVE.value,
            DomainJsonConverter(),
            {
                'name': 'Domain JSON',
                'description': 'Canonical format for diagram structure and execution',
                'extension': '.json',
                'supports_import': True,
                'supports_export': True
            }
        )
        
        # Light YAML
        self.register(
            DiagramFormat.LIGHT.value,
            LightYamlConverter(),
            {
                'name': 'Light YAML',
                'description': 'Simplified format using labels instead of IDs',
                'extension': '.light.yaml',
                'supports_import': True,
                'supports_export': True
            }
        )
        
        # Readable YAML
        self.register(
            DiagramFormat.READABLE.value,
            ReadableYamlConverter(),
            {
                'name': 'Readable Workflow',
                'description': 'Human-friendly workflow format',
                'extension': '.readable.yaml',
                'supports_import': True,
                'supports_export': True
            }
        )
    
    def register(self, format_id: str, converter: DiagramConverter, 
                info: Dict[str, str]):
        """Register a converter with metadata."""
        self._converters[format_id] = converter
        self._format_info[format_id] = info
    
    def get(self, format_id: str) -> Optional[DiagramConverter]:
        """Get converter by format ID."""
        return self._converters.get(format_id)
    
    def get_info(self, format_id: str) -> Optional[Dict[str, str]]:
        """Get format metadata."""
        return self._format_info.get(format_id)
    
    def list_formats(self) -> List[Dict[str, str]]:
        """List all registered formats with their info."""
        return [
            {'id': fmt_id, **info}
            for fmt_id, info in self._format_info.items()
        ]
    
    def detect_format(self, content: str) -> Optional[str]:
        """
        Automatically detect format from content.
        Returns the format ID with highest confidence.
        """
        confidences: List[Tuple[str, float]] = []
        
        for format_id, converter in self._converters.items():
            try:
                confidence = converter.detect_format_confidence(content)
                confidences.append((format_id, confidence))
            except:
                confidences.append((format_id, 0.0))
        
        # Sort by confidence
        confidences.sort(key=lambda x: x[1], reverse=True)
        
        # Return format with highest confidence if > 0.5
        if confidences and confidences[0][1] > 0.5:
            return confidences[0][0]
        
        return None
    
    def get_export_formats(self) -> List[Dict[str, str]]:
        """Get formats that support export."""
        return [
            {'id': fmt_id, **info}
            for fmt_id, info in self._format_info.items()
            if info.get('supports_export', True)
        ]
    
    def get_import_formats(self) -> List[Dict[str, str]]:
        """Get formats that support import."""
        return [
            {'id': fmt_id, **info}
            for fmt_id, info in self._format_info.items()
            if info.get('supports_import', True)
        ]


# Global registry instance
converter_registry = ConverterRegistry()