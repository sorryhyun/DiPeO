"""Base conversion strategy with common logic for all diagram formats."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from dipeo.diagram_generated import DomainDiagram

from dipeo.domain.diagram.ports import FormatStrategy
from dipeo.domain.diagram.utils import (
    extract_common_arrows,
    PersonExtractor,
    ArrowDataProcessor,
    HandleParser,
    NodeFieldMapper,
    process_dotted_keys,
)

log = logging.getLogger(__name__)


class BaseConversionStrategy(FormatStrategy, ABC):
    """Template Method pattern for diagram conversion with customizable node/arrow extraction."""

    @abstractmethod
    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        """Serialize a DomainDiagram to string format.
        
        Args:
            diagram: The DomainDiagram to serialize
            
        Returns:
            String representation in the target format
        """
        pass
    
    @abstractmethod
    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        """Deserialize string content to a DomainDiagram.
        
        Args:
            content: String content to deserialize
            diagram_path: Optional path to the diagram file for context (e.g., prompt resolution)
            
        Returns:
            DomainDiagram instance
        """
        pass
    
    @abstractmethod
    def parse(self, content: str) -> Any:
        """Parse string content to intermediate format.
        
        Override in subclasses for format-specific parsing.
        """
        pass
    
    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data to string representation.
        
        Override in subclasses for format-specific formatting.
        """
        pass
    

    def detect_confidence(self, data: dict[str, Any]) -> float:
        """Detect confidence level for this format.
        
        Override in subclasses for format-specific detection.
        """
        return 0.5
    
    def quick_match(self, content: str) -> bool:
        """Quick check if content matches this format.
        
        Override in subclasses for better performance.
        """
        try:
            self.parse(content)
            return True
        except Exception:
            return False
    
    def _clean_graphql_fields(self, data: Any) -> Any:
        """Remove GraphQL-specific fields from data."""
        if isinstance(data, dict):
            return {
                k: self._clean_graphql_fields(v) 
                for k, v in data.items() 
                if not k.startswith('__')
            }
        elif isinstance(data, list):
            return [self._clean_graphql_fields(item) for item in data]
        else:
            return data