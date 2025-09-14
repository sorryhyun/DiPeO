"""Base conversion strategy with common logic for all diagram formats."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.ports import FormatStrategy

log = logging.getLogger(__name__)


class BaseConversionStrategy(FormatStrategy, ABC):
    """Template Method pattern for diagram conversion with customizable node/arrow extraction."""

    @abstractmethod
    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        """Serialize a DomainDiagram to string format."""
        pass

    @abstractmethod
    def deserialize_to_domain(self, content: str, diagram_path: str | None = None) -> DomainDiagram:
        """Deserialize string content to a DomainDiagram."""
        pass

    @abstractmethod
    def parse(self, content: str) -> Any:
        """Parse string content to intermediate format."""
        pass

    @abstractmethod
    def format(self, data: Any) -> str:
        """Format data to string representation."""
        pass

    def detect_confidence(self, data: dict[str, Any]) -> float:
        """Detect confidence level for this format."""
        return 0.5

    def quick_match(self, content: str) -> bool:
        """Quick check if content matches this format."""
        try:
            self.parse(content)
            return True
        except Exception:
            return False

    def _clean_graphql_fields(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: self._clean_graphql_fields(v) for k, v in data.items() if not k.startswith("__")
            }
        elif isinstance(data, list):
            return [self._clean_graphql_fields(item) for item in data]
        else:
            return data
