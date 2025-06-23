"""Simplified registry using UnifiedDiagramConverter directly."""

from .unified_converter import UnifiedDiagramConverter

# The registry is now just an instance of UnifiedDiagramConverter
# This acts as both a facade and the actual converter
converter_registry = UnifiedDiagramConverter()

# Add backward compatibility methods if needed
converter_registry.list_formats = converter_registry.get_supported_formats
converter_registry.convert = lambda content, from_format, to_format: converter_registry.serialize(
    converter_registry.deserialize(content, from_format), to_format
)

# Add get method for backward compatibility
def _get(self, format_id):
    """Get converter for format (backward compatibility)."""
    if format_id in self.strategies:
        self.set_format(format_id)
        return self
    return None

converter_registry.get = _get.__get__(converter_registry)

# Add get_info method for backward compatibility
def _get_info(self, format_id):
    """Get format info (backward compatibility)."""
    strategy = self.strategies.get(format_id)
    return strategy.format_info if strategy else None

converter_registry.get_info = _get_info.__get__(converter_registry)
