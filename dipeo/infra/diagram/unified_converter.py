# Unified converter that uses format strategies

import logging

from dipeo.models import DomainDiagram

DomainDiagram.model_rebuild()

from dipeo.core.ports import DiagramConverter, FormatStrategy
from dipeo.domain.diagram.strategies import LightYamlStrategy, NativeJsonStrategy, ReadableYamlStrategy

logger = logging.getLogger(__name__)


class UnifiedDiagramConverter(DiagramConverter):
    # Universal converter using strategy pattern for different formats

    def __init__(self):
        self.strategies: dict[str, FormatStrategy] = {}
        self._register_default_strategies()

    def _register_default_strategies(self):
        self.register_strategy(NativeJsonStrategy())
        self.register_strategy(LightYamlStrategy())
        self.register_strategy(ReadableYamlStrategy())

    def register_strategy(self, strategy: FormatStrategy):
        self.strategies[strategy.format_id] = strategy

    def set_format(self, format_id: str):
        """Set the active format for conversion."""
        if format_id not in self.strategies:
            raise ValueError(f"Unknown format: {format_id}")
        self.active_format = format_id

    def get_strategy(self, format_id: str | None = None) -> FormatStrategy:
        """Get strategy for the specified format."""
        fmt = format_id or getattr(self, "active_format", None)
        if not fmt:
            raise ValueError("No format specified")

        strategy = self.strategies.get(fmt)
        if not strategy:
            raise ValueError(f"Unknown format: {fmt}")

        return strategy

    def serialize(self, diagram: DomainDiagram, format_id: str | None = None) -> str:
        """Convert domain diagram to format-specific string."""
        fmt = format_id or getattr(self, "active_format", None)
        if not fmt:
            raise ValueError("No format specified for serialization")

        strategy = self.get_strategy(fmt)
        return strategy.serialize_from_domain(diagram)

    def deserialize(self, content: str, format_id: str | None = None) -> DomainDiagram:
        """Convert format-specific string to domain diagram."""
        fmt = format_id or getattr(self, "active_format", None)

        if not fmt:
            fmt = self.detect_format(content)
            if not fmt:
                raise ValueError("Could not detect format automatically")

        strategy = self.get_strategy(fmt)
        return strategy.deserialize_to_domain(content)


    def validate(
        self, content: str, format_id: str | None = None
    ) -> tuple[bool, list[str]]:
        """Validate content without full deserialization."""
        try:
            self.deserialize(content, format_id)
            return True, []
        except Exception as e:
            return False, [str(e)]

    def detect_format(self, content: str) -> str | None:
        """Automatically detect format from content."""
        # First try quick match for efficiency
        for format_id, strategy in self.strategies.items():
            if strategy.quick_match(content):
                return format_id

        # Fall back to full parsing if no quick match
        confidences: list[tuple[str, float]] = []

        for format_id, strategy in self.strategies.items():
            try:
                data = strategy.parse(content)
                confidence = strategy.detect_confidence(data)
                confidences.append((format_id, confidence))
            except Exception:
                confidences.append((format_id, 0.0))

        confidences.sort(key=lambda x: x[1], reverse=True)

        if confidences and confidences[0][1] > 0.5:
            return confidences[0][0]

        return None

    def detect_format_confidence(self, content: str) -> float:
        format_id = self.detect_format(content)
        if format_id:
            return 1.0
        return 0.0

    def get_supported_formats(self) -> list[dict[str, str]]:
        return [
            {"id": format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
        ]

    def get_export_formats(self) -> list[dict[str, str]]:
        return [
            {"id": format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
            if strategy.format_info.get("supports_export", True)
        ]

    def get_import_formats(self) -> list[dict[str, str]]:
        return [
            {"id": format_id, **strategy.format_info}
            for format_id, strategy in self.strategies.items()
            if strategy.format_info.get("supports_import", True)
        ]

    def convert(self, content: str, from_format: str, to_format: str) -> str:
        """Convert content from one format to another."""
        diagram = self.deserialize(content, from_format)
        return self.serialize(diagram, to_format)

    def get(self, format_id: str) -> FormatStrategy:
        """Get strategy for the specified format (alias for get_strategy)."""
        return self.get_strategy(format_id)

    def get_info(self, format_id: str) -> dict[str, str]:
        """Get format information for the specified format."""
        strategy = self.get_strategy(format_id)
        return strategy.format_info


# Create a singleton instance to act as the registry
converter_registry = UnifiedDiagramConverter()
