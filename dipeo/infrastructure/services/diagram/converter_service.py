"""Diagram converter service using strategy pattern for different formats."""

import logging
from typing import Dict

from dipeo.core import BaseService
from dipeo.core.ports import DiagramStorageSerializer, FormatStrategy
from dipeo.domain.diagram.strategies import (
    LightYamlStrategy,
    NativeJsonStrategy,
    ReadableYamlStrategy,
    ExecutableJsonStrategy,
)
from dipeo.diagram_generated import DomainDiagram

logger = logging.getLogger(__name__)


class DiagramConverterService(BaseService, DiagramStorageSerializer):
    """Converts diagrams between different formats using pluggable strategies."""
    
    def __init__(self):
        super().__init__()
        self.strategies: Dict[str, FormatStrategy] = {}
        self._initialized = False
        self.active_format: str | None = None
    
    async def initialize(self) -> None:
        if self._initialized:
            return
            
        self._register_default_strategies()
        self._initialized = True
    
    def _register_default_strategies(self) -> None:
        self.register_strategy(NativeJsonStrategy())
        self.register_strategy(LightYamlStrategy())
        self.register_strategy(ReadableYamlStrategy())
        self.register_strategy(ExecutableJsonStrategy())
    
    def register_strategy(self, strategy: FormatStrategy) -> None:
        self.strategies[strategy.format_id] = strategy
    
    def set_format(self, format_id: str) -> None:
        if format_id not in self.strategies:
            raise ValueError(f"Unknown format: {format_id}")
        self.active_format = format_id
    
    def get_strategy(self, format_id: str | None = None) -> FormatStrategy:
        fmt = format_id or self.active_format
        if not fmt:
            raise ValueError("No format specified")
        
        strategy = self.strategies.get(fmt)
        if not strategy:
            raise ValueError(f"Unknown format: {fmt}")
        
        return strategy
    
    def serialize_for_storage(self, diagram: DomainDiagram, format: str) -> str:
        """Serialize a DomainDiagram to string for file storage.
        
        Args:
            diagram: The DomainDiagram to serialize
            format: Target format ('native', 'light', 'readable')
            
        Returns:
            String representation for file storage
        """
        if not self._initialized:
            raise RuntimeError("DiagramConverterService not initialized")
            
        strategy = self.get_strategy(format)
        return strategy.serialize_from_domain(diagram)
    
    def deserialize_from_storage(self, content: str, format: str | None = None) -> DomainDiagram:
        """Deserialize file content to DomainDiagram.
        
        Args:
            content: String content from file
            format: Optional format hint, will auto-detect if not provided
            
        Returns:
            DomainDiagram instance
        """
        if not self._initialized:
            raise RuntimeError("DiagramConverterService not initialized")
            
        fmt = format
        
        if not fmt:
            fmt = self.detect_format(content)
            if not fmt:
                raise ValueError("Could not detect format automatically")
        
        strategy = self.get_strategy(fmt)
        return strategy.deserialize_to_domain(content)

    def validate(
        self, content: str, format_id: str | None = None
    ) -> tuple[bool, list[str]]:
        if not self._initialized:
            return False, ["DiagramConverterService not initialized"]
            
        try:
            self.deserialize_from_storage(content, format_id)
            return True, []
        except Exception as e:
            return False, [str(e)]
    
    def detect_format(self, content: str) -> str | None:
        if not self._initialized:
            logger.warning("Attempting format detection on uninitialized service")
            return None
            
        for format_id, strategy in self.strategies.items():
            if strategy.quick_match(content):
                return format_id
        
        confidences: list[tuple[str, float]] = []
        
        for format_id, strategy in self.strategies.items():
            try:
                data = strategy.parse(content)
                confidence = strategy.detect_confidence(data)
                confidences.append((format_id, confidence))
            except Exception as e:
                logger.debug(f"Failed to parse as {format_id}: {e}")
                confidences.append((format_id, 0.0))
        
        confidences.sort(key=lambda x: x[1], reverse=True)
        
        if confidences and confidences[0][1] > 0.5:
            detected_format = confidences[0][0]
            logger.debug(
                f"Detected format: {detected_format} "
                f"(confidence: {confidences[0][1]:.2f})"
            )
            return detected_format
        
        return None
    
    def list_supported_formats(self) -> list[str]:
        return list(self.strategies.keys())
    
    def can_convert(self, from_format: str, to_format: str) -> bool:
        return from_format in self.strategies and to_format in self.strategies
    
    def get_supported_formats(self) -> list[dict[str, str]]:
        formats = []
        for format_id, strategy in self.strategies.items():
            if hasattr(strategy, 'format_info'):
                format_data = {"id": format_id, **strategy.format_info}
                formats.append(format_data)
            else:
                formats.append({
                    "id": format_id,
                    "name": format_id.title(),
                    "description": f"{format_id} format",
                    "extension": f".{format_id}",
                    "supports_import": True,
                    "supports_export": True,
                })
        return formats
    
    def list_formats(self) -> list[dict[str, str]]:
        return self.get_supported_formats()